#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sinh ngân hàng câu hỏi trắc nghiệm từ vocab.json (kho từ vựng tài chính - ngân hàng).

Luu vao questions.json co cau truc:
{
  "0": [ {...}, ... ],   # de 0 ... de 9 (10 de)
}
Moi cau:
{
  "id": "Q0001",           # ma cau toan cuc
  "term": str,             # tu khoa chinh
  "type": "A|B|C|D",       # loai hoi (duoi doc)
  "stem": str,             # noi dung cau hoi
  "options": [str,str,str,str],  # 4 dap an (dung o vi tri correct_letter)
  "correct_letter": "A|B|C|D",
  "explanation": str,      # giai thich (hien thi sau khi nop bai)
  "test_id": int           # de nam (0-9)
}

4 loai hoi (muc do cao):
  A: nhan biet tu (term -> nghia tieng Viet)
  B: dau nghia (nghia tieng Viet -> chon term)
  C: dai hieu (dinh nghia tieng Anh -> chon term)
  D: hieu nghia anh -> (term -> chon dinh nghia tieng Anh dung)
"""

import json
import random
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
VOCAB_PATH = os.path.join(BASE, "vocab.json")
OUT_PATH = os.path.join(BASE, "questions.json")

NUM_TESTS = 10
Q_PER_TEST = 60
SEED = 42  # co dinh de co the tai tai lai / sua doi de khi can

random.seed(SEED)


def load_vocab():
    with open(VOCAB_PATH, encoding="utf-8") as f:
        data = json.load(f)
    # bo trung lap theo term, giu thu tu
    seen = set()
    uniq = []
    for t in data:
        term = (t.get("term") or "").strip()
        if not term or term in seen:
            continue
        seen.add(term)
        uniq.append({
            "term": term,
            "def_en": (t.get("def_en") or "").strip(),
            "mean_vi": (t.get("mean_vi") or "").strip(),
        })
    return uniq


def pick_distractors(correct_text, pool, k=3, avoid_empty=True):
    """Chon k phan tu khac correct_text tu pool, tra ve danh sach."""
    pool = [p for p in pool if p and p.strip() and p.strip() != correct_text]
    random.shuffle(pool)
    chosen = pool[:k]
    while len(chosen) < k:
        chosen.append(f"(dap an {len(chosen)+1})")
    return chosen


def build_pool(vocab):
    """Tat ca cau hoi tu tat ca tu vong (tối đa 4 cau/tu)."""
    terms = [t["term"] for t in vocab]
    mean_pool = [t["mean_vi"] for t in vocab if t["mean_vi"]]
    def_pool = [t["def_en"] for t in vocab if t["def_en"]]

    pool = []
    qid = 1
    for idx, t in enumerate(vocab):
        term = t["term"]
        mean = t["mean_vi"]
        definition = t["def_en"]
        test_id = idx % NUM_TESTS

        # Loai A: term -> nghia tieng Viet
        if mean:
            opts = [mean] + pick_distractors(mean, mean_pool, 3)
            random.shuffle(opts)
            correct = opts.index(mean)
            pool.append({
                "id": f"Q{qid:04d}", "term": term, "type": "A",
                "stem": f"Tu '{term}' trong tai chinh - ngan hang co nghia nao sau day?",
                "options": opts,
                "correct_letter": "ABCD"[correct],
                "explanation": f"'{term}' = {mean}",
                "test_id": test_id,
            })
            qid += 1

        # Loai B: nghia tieng Viet -> term
        if mean:
            opts = [term] + pick_distractors(term, terms, 3)
            random.shuffle(opts)
            correct = opts.index(term)
            pool.append({
                "id": f"Q{qid:04d}", "term": term, "type": "B",
                "stem": f"Thuat ngu tieng Anh nao sau day co nghia: '{mean}'?",
                "options": opts,
                "correct_letter": "ABCD"[correct],
                "explanation": f"Nghia '{mean}' duong dan den '{term}'",
                "test_id": test_id,
            })
            qid += 1

        # Loai C: dinh nghia tieng Anh -> term
        if definition:
            opts = [term] + pick_distractors(term, terms, 3)
            random.shuffle(opts)
            correct = opts.index(term)
            pool.append({
                "id": f"Q{qid:04d}", "term": term, "type": "C",
                "stem": f"Thuat ngu tieng Anh nao co dinh nghia: '{definition}'?",
                "options": opts,
                "correct_letter": "ABCD"[correct],
                "explanation": f"Dinh nghia cua '{term}': {definition}",
                "test_id": test_id,
            })
            qid += 1

        # Loai D: term -> chon dinh nghia tieng Anh dung
        if definition:
            opts = [definition] + pick_distractors(definition, def_pool, 3)
            random.shuffle(opts)
            correct = opts.index(definition)
            pool.append({
                "id": f"Q{qid:04d}", "term": term, "type": "D",
                "stem": f"Tu '{term}' co dinh nghia tieng Anh nao sau day?",
                "options": opts,
                "correct_letter": "ABCD"[correct],
                "explanation": f"'{term}': {definition}",
                "test_id": test_id,
            })
            qid += 1

    return pool


def balance_letters(questions):
    """
    Sap xep lai vi tri dap an dung cua tung cau sao cho trong 60 cau mot de,
    dung dung 15 lan tai A, B, C, D (phan bo deu toan bo).
    """
    letters = ["A", "B", "C", "D"]
    # sap xep cau theo ID de co thu tu co dinh
    questions = sorted(questions, key=lambda q: q["id"])
    for i, q in enumerate(questions):
        target = letters[i % 4]
        cur = q["correct_letter"]
        if cur == target:
            continue
        # chuyen dap an dung (cur) sang vi tri target; giu thu tu cac dap an con lai
        cur_i = letters.index(cur)
        tgt_i = letters.index(target)
        opts = q["options"]
        correct_text = opts[cur_i]
        # xoa dap an dung khoi vi tri cu, chen vao vi tri target
        new_opts = [o for o in opts if o != correct_text]
        new_opts.insert(tgt_i, correct_text)
        q["options"] = new_opts
        q["correct_letter"] = target
    return questions


def select_for_test(pool, test_id):
    """Chon 60 cau cho mot de: dam bao moi tu gắn voi de xuat hien it nhat 1 lan."""
    assigned = [q for q in pool if q["test_id"] == test_id]
    # gom theo term
    by_term = {}
    for q in assigned:
        by_term.setdefault(q["term"], []).append(q)

    chosen = []
    used_ids = set()
    # buoc 1: 1 cau moi term (xuan suan loai theo vong)
    types_order = ["A", "B", "C", "D"]
    for term, qs in by_term.items():
        # chon loai khac nhau theo test_id de cac de khong giong nhau
        pref_type = types_order[test_id % 4]
        cand = [q for q in qs if q["type"] == pref_type] or qs
        q = random.choice(cand)
        chosen.append(q)
        used_ids.add(q["id"])

    # buoc 2: bo sung den 60 cau tu cac cau con lai cua cung de
    remaining = [q for q in assigned if q["id"] not in used_ids]
    random.shuffle(remaining)
    need = Q_PER_TEST - len(chosen)
    chosen += remaining[:need]

    # neu du 60 (co the xay ra neu it tu), bo sung tu pool toan cuc khac de
    if len(chosen) < Q_PER_TEST:
        others = [q for q in pool if q["test_id"] != test_id and q["id"] not in used_ids]
        random.shuffle(others)
        chosen += others[:(Q_PER_TEST - len(chosen))]

    chosen = chosen[:Q_PER_TEST]
    return balance_letters(chosen)


def main():
    vocab = load_vocab()
    print(f"Co {len(vocab)} tu vong (khong trung lap).")

    pool = build_pool(vocab)
    print(f"Tong so cau hoi sinh duoc: {len(pool)}")

    tests = {}
    for tid in range(NUM_TESTS):
        qs = select_for_test(pool, tid)
        # kiem tra cover tat ca tu gắn voi de
        covered_terms = sorted({q["term"] for q in qs})
        tests[str(tid)] = qs
        # dem so tu ung voi test nay trong vocab
        vocab_terms_for_test = sorted({t["term"] for i, t in enumerate(vocab) if i % NUM_TESTS == tid})
        print(f"De {tid}: {len(qs)} cau | tu gắn: {len(vocab_terms_for_test)} | co trong de: {len(covered_terms)} | "
              f"phan bo A/B/C/D: " +
              f"A={sum(1 for q in qs if q['correct_letter']=='A')} B={sum(1 for q in qs if q['correct_letter']=='B')} "
              f"C={sum(1 for q in qs if q['correct_letter']=='C')} D={sum(1 for q in qs if q['correct_letter']=='D')}")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(tests, f, ensure_ascii=False, indent=2)
    print(f"Da luu {OUT_PATH} (10 de x {Q_PER_TEST} cau).")


if __name__ == "__main__":
    main()
