/* AVCN - front-end lam bai trac nghiem */
(function(){
  const TEST_ID = window.TEST_ID || (typeof TEST_ID !== "undefined" ? TEST_ID : null);
  const TIME_SEC = window.TIME_SEC || (typeof TIME_SEC !== "undefined" ? TIME_SEC : 90*60);
  const USER_KEY = "avcn_user_" + TEST_ID;
  const userNameEl = document.getElementById("userName");
  const timerEl = document.getElementById("timer");
  const form = document.getElementById("testForm");
  const questionsEl = document.getElementById("questions");
  const progressBar = document.getElementById("progressBar");
  const progressText = document.getElementById("progressText");
  const progressWrap = document.querySelector(".progress");
  const btnSave = document.getElementById("btnSave");
  const btnSubmit = document.getElementById("btnSubmit");
  const msg = document.getElementById("msg");

  // luu ten nguoi dung (co su dung lai)
  const saved = localStorage.getItem(window.USER_KEY);
  if (saved) userNameEl.value = saved;

  let questions = [];
  let startTime = null;
  let timerId = null;
  let answered = {}; // qid -> letter

  // khoi phuc trang thai da luu (neu co)
  function loadState(){
    try {
      const a = localStorage.getItem(USER_KEY + "_ans");
      if (a) answered = JSON.parse(a);
    } catch(e){}
  }
  loadState();

  function showMsg(text, kind){
    msg.textContent = text;
    msg.className = "msg " + (kind || "");
    msg.style.display = text ? "block" : "none";
  }

  function render(){
    questionsEl.innerHTML = "";
    questions.forEach((q, i) => {
      const box = document.createElement("div");
      box.className = "item";
      box.dataset.qid = q.id;
      box.innerHTML = `
        <h4>Cau ${i+1} <span class="loai">${q.type}</span></h4>
        <div class="stem">${escapeHtml(q.stem)}</div>
        <div class="opts">
          ${q.options.map((opt, oi) => {
            const letter = "ABCD"[oi];
            const checked = answered[q.id] === letter ? "checked" : "";
            return `<label class="opt"><input type="radio" name="q_${q.id}" value="${letter}" ${checked}> <span class="letter">${letter}</span>. ${escapeHtml(opt)}</label>`;
          }).join("")}
        </div>`;
      box.querySelectorAll("input[type=radio]").forEach(radio => {
        radio.addEventListener("change", () => { answered[q.id] = radio.value; updateProgress(); persist(); });
      });
      questionsEl.appendChild(box);
    });
    updateProgress();
  }

  function updateProgress(){
    const total = questions.length;
    const done = Object.keys(answered).length;
    if (progressBar){ progressBar.style.width = Math.round(done/total*100) + "%"; }
    if (progressText){ progressText.textContent = done + " / " + total + " cau da tra loi"; }
  }

  function persist(){
    localStorage.setItem(USER_KEY + "_ans", JSON.stringify(answered));
    localStorage.setItem(USER_KEY + "_name", userNameEl.value.trim());
    if (userNameEl.value.trim()) localStorage.setItem(USER_KEY, userNameEl.value.trim());
  }

  

  // ---------- timer ----------
  function fmt(sec){
    const h = Math.floor(sec/3600);
    const m = Math.floor((sec%3600)/60);
    const s = sec%60;
    return (h?h+":":"") + String(m).padStart(2,"0") + ":" + String(s).padStart(2,"0");
  }
  function tick(){
    if (!startTime) return;
    const left = TIME_SEC - Math.floor((Date.now() - startTime)/1000);
    if (left <= 0){
      timerEl.textContent = "00:00:00";
      timerEl.classList.add("expire");
      clearInterval(timerId);
      showMsg("Het thoi gian! Bai se duoc nop tu dong.", "err");
      setTimeout(() => form.dispatchEvent(new Event("submit")), 800);
      return;
    }
    timerEl.textContent = fmt(left);
    timerEl.classList.remove("expire");
  }

  // ---------- submit ----------
  async function submitTest(ev){
    ev.preventDefault();
    const name = userNameEl.value.trim();
    if (!name){ showMsg("Vui long nhap ten cua ban.", "err"); userNameEl.focus(); return false; }
    persist();
    clearInterval(timerId);

    const payload = {
      test_id: TEST_ID,
      user_name: name,
      answers: answered,
      started_at: startTime ? new Date(startTime).toISOString() : new Date().toISOString(),
    };

    btnSubmit.disabled = true;
    btnSubmit.textContent = "Dang nop...";
    showMsg("");

    try {
      const res = await fetch("/api/submit", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Loi nop bai");
      // luu ket qua va chuyen trang
      localStorage.setItem("avcn_last_attempt", data.attempt_id);
      window.location.href = "/result/" + data.attempt_id;
    } catch (e){
      showMsg(e.message, "err");
      btnSubmit.disabled = false;
      btnSubmit.textContent = "Nop bai va xem ket qua";
      return false;
    }
    return false;
  }

  async function init(){
    try {
      const res = await fetch("/api/questions/" + TEST_ID);
      const data = await res.json();
      if (!data.questions) throw new Error("Khong tai duoc cau hoi");
      questions = data.questions;
      startTime = new Date();
      render();
      timerId = setInterval(tick, 1000);
      tick();
    } catch (e){
      showMsg("Loi tai cau hoi: " + e.message, "err");
    }
  }

  form.addEventListener("submit", submitTest);
  btnSave.addEventListener("click", () => { persist(); showMsg("Da luu tam trinh duyet.", "ok"); setTimeout(()=>showMsg(""), 1500); });
  userNameEl.addEventListener("input", persist);

  window.addEventListener("beforeunload", () => persist());

  init();
})();

function escapeHtml(s){
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}
