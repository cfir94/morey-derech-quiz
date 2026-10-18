#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Checks a set of tour-guide practice exams for the defects this material is
prone to. Every check here exists because a question that broke it shipped.

Usage:
    python3 check_exam.py exams.json [--items 50] [--strict]

Input is a JSON object keyed by exam id:

    {
      "focus_1": {
        "title": "מבחן דגשי הרכז 1",
        "items": [
          {"type": "mc",   "topic": "...", "q": "...",
           "options": ["...", "...", "...", "..."], "correct": 2, "exp": "..."},
          {"type": "fill", "topic": "...", "q": "... ___ ", "answer": "...", "exp": "..."}
        ]
      }
    }

Exit code is 0 when nothing blocking was found, 1 otherwise. Warnings do not
fail the run unless --strict is passed; they are judgement calls a human should
look at, not automatic defects.
"""

import argparse
import json
import re
import sys
from collections import Counter

# ---------------------------------------------------------------- helpers

# a parenthetical carrying a year, a century or an era marker
DATE_IN_TEXT = re.compile(r'\((?:[^)]*?(?:מאה|מאות|לספירה|לפנה|\d{3,4})[^)]*)\)')
# questions whose whole job is ordering, where a printed date gives it away
ORDERING_Q = re.compile(r'מאוחר יותר|הכי מוקדם|המוקדם|קרה ראשון|קרה קודם|קדם|הסדר הכרונולוגי')
# negative questions, where every distractor must fail the predicate
NEGATIVE_Q = re.compile(r'\bאינו\b|\bאינה\b|\bאינם\b|\bלא נמצא|\bלא שייך|שאינו|שאינה')
BLANK = re.compile(r'_{3,}')


def words(s):
    return [w for w in re.split(r'\s+', s.strip()) if w]


def norm(s):
    """Collapse whitespace and strip the blank run, for duplicate detection."""
    return re.sub(r'\s+', ' ', BLANK.sub(' ', s)).strip()


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def err(self, exam, idx, msg):
        self.errors.append("[%s #%s] %s" % (exam, idx, msg))

    def warn(self, exam, idx, msg):
        self.warnings.append("[%s #%s] %s" % (exam, idx, msg))


# ---------------------------------------------------------------- checks

def check_item(rep, exam, i, it):
    n = i + 1
    q = it.get("q", "")
    exp = it.get("exp", "")
    kind = it.get("type")

    if kind not in ("mc", "fill"):
        rep.err(exam, n, "unknown type %r" % kind)
        return
    if not q.strip():
        rep.err(exam, n, "empty question")

    # An explanation is the only feedback a student gets when wrong.
    if not exp.strip():
        rep.err(exam, n, "no explanation")
    elif len(exp.strip()) < 25:
        rep.warn(exam, n, "explanation is very short (%d chars): %r" % (len(exp.strip()), exp[:60]))

    if kind == "fill":
        ans = (it.get("answer") or "").strip()
        if not ans:
            rep.err(exam, n, "fill item with no answer")
            return
        if not BLANK.search(q):
            rep.warn(exam, n, "fill item has no visible blank (___) in the question")
        w = len(words(ans))
        # The coordinator's rule: one word to three. A sentence means the
        # question is really an essay question in disguise.
        if w > 3:
            rep.err(exam, n, "fill answer is %d words (max 3): %r" % (w, ans))
        # The answer sitting verbatim in the question stem gives it away.
        stem = norm(q)
        if len(ans) > 3 and ans in stem:
            rep.err(exam, n, "the answer %r appears in the question itself" % ans)
        return

    # ---- multiple choice ----
    opts = it.get("options") or []
    ci = it.get("correct")

    if len(opts) != 4:
        rep.err(exam, n, "%d options (expected 4)" % len(opts))
    if not isinstance(ci, int) or not (0 <= ci < len(opts)):
        rep.err(exam, n, "correct index %r out of range" % ci)
        return
    if any(not o.strip() for o in opts):
        rep.err(exam, n, "an option is empty")
    dupes = [o for o, c in Counter(o.strip() for o in opts).items() if c > 1]
    if dupes:
        rep.err(exam, n, "duplicate options: %s" % dupes)

    correct = opts[ci]
    distractors = [o for k, o in enumerate(opts) if k != ci]

    # Length silhouette: a conspicuously long correct answer is guessable
    # without reading it. Short options carry no real signal, so skip them.
    if distractors:
        mean_d = sum(len(o) for o in distractors) / len(distractors)
        if len(correct) > 20 and mean_d > 0 and len(correct) > 1.5 * mean_d:
            rep.warn(exam, n, "correct answer %.1fx longer than the mean distractor "
                              "(%d vs %d chars)" % (len(correct) / mean_d, len(correct), round(mean_d)))

    # An ordering question that prints the dates answers itself.
    if ORDERING_Q.search(q):
        dated = [o for o in opts if DATE_IN_TEXT.search(o)]
        if len(dated) >= 2:
            rep.err(exam, n, "ordering question prints dates in %d options — it answers "
                             "itself; move the dates into the explanation" % len(dated))

    # Only the correct answer carrying a qualifier marks it by shape.
    only_correct_dated = DATE_IN_TEXT.search(correct) and not any(
        DATE_IN_TEXT.search(o) for o in distractors)
    if only_correct_dated:
        rep.warn(exam, n, "only the correct answer carries a date/qualifier — "
                          "the extra specificity marks it")

    # Negative questions are where two-correct-answer bugs live.
    if NEGATIVE_Q.search(q):
        rep.warn(exam, n, "negative question — verify by hand that every distractor "
                          "fails the predicate as literally worded")

    # An option repeated verbatim in the stem is a giveaway.
    stem = norm(q)
    if len(correct) > 6 and correct.strip() in stem:
        rep.err(exam, n, "the correct option appears verbatim in the question")


def check_exam(rep, name, exam, want_items):
    items = exam.get("items") or []
    if not exam.get("title", "").strip():
        rep.warn(name, "-", "exam has no title")

    if want_items and len(items) != want_items:
        rep.err(name, "-", "%d items (expected %d)" % (len(items), want_items))

    mc = [i for i in items if i.get("type") == "mc"]
    fill = [i for i in items if i.get("type") == "fill"]
    if items:
        share = len(fill) / len(items)
        # The real exam runs about 12 fill-ins in 50, i.e. ~24%.
        if not (0.15 <= share <= 0.35):
            rep.warn(name, "-", "fill-in share is %.0f%% (%d of %d); the real exam runs ~24%%"
                     % (100 * share, len(fill), len(items)))

    for i, it in enumerate(items):
        check_item(rep, name, i, it)

    # Answer-position balance. Hand-written exams drift toward the middle.
    pos = Counter(i["correct"] for i in mc
                  if isinstance(i.get("correct"), int) and 0 <= i["correct"] < 4)
    if len(pos) and sum(pos.values()) >= 12:
        tot = sum(pos.values())
        worst, cnt = pos.most_common(1)[0]
        if cnt / tot > 0.45:
            rep.err(name, "-", "answer position %d holds %.0f%% of the %d MC answers — shuffle them"
                    % (worst + 1, 100 * cnt / tot, tot))
        elif cnt / tot > 0.35:
            rep.warn(name, "-", "answer position %d holds %.0f%% of the %d MC answers"
                     % (worst + 1, 100 * cnt / tot, tot))
        missing = [p for p in range(4) if p not in pos]
        if missing:
            rep.err(name, "-", "no correct answer ever sits at position(s) %s"
                    % ", ".join(str(p + 1) for p in missing))

    # Topic spread, so one subject doesn't quietly dominate.
    buckets = Counter(re.split(r' [–—-] ', i.get("topic", "?"))[0] for i in items)
    if items and len(buckets) > 1:
        top, cnt = buckets.most_common(1)[0]
        if cnt / len(items) > 0.55:
            rep.warn(name, "-", "topic %r is %.0f%% of the exam" % (top, 100 * cnt / len(items)))
    return buckets


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--items", type=int, default=50,
                    help="expected items per exam (0 to skip the check)")
    ap.add_argument("--strict", action="store_true",
                    help="treat warnings as failures too")
    args = ap.parse_args()

    with open(args.path, encoding="utf-8") as f:
        data = json.load(f)

    rep = Report()
    seen = {}           # normalised question -> "exam #n", across all exams
    all_buckets = Counter()

    for name, exam in data.items():
        all_buckets += check_exam(rep, name, exam, args.items)
        for i, it in enumerate(exam.get("items") or []):
            key = norm(it.get("q", ""))
            if not key:
                continue
            where = "%s #%d" % (name, i + 1)
            if key in seen:
                # Repeating a question across exams wastes one of 50 slots and
                # lets a student coast on recall of the practice, not the fact.
                rep.err(name, i + 1, "duplicate of %s: %r" % (seen[key], key[:70]))
            else:
                seen[key] = where

    n_items = sum(len(e.get("items") or []) for e in data.values())
    print("checked %d exam(s), %d items" % (len(data), n_items))
    if all_buckets:
        print("topics: " + ", ".join("%s=%d" % kv for kv in all_buckets.most_common()))

    if rep.warnings:
        print("\nwarnings (%d) — judgement calls, read them:" % len(rep.warnings))
        for w in rep.warnings:
            print("  ! " + w)
    if rep.errors:
        print("\nerrors (%d) — fix these:" % len(rep.errors))
        for e in rep.errors:
            print("  x " + e)
        return 1
    if args.strict and rep.warnings:
        print("\n--strict: failing on warnings")
        return 1
    print("\nno blocking problems found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
