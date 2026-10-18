---
name: morey-derech-exam
description: Writes Hebrew practice exams (מבחני תרגול / מבחני הכנה) for the Israeli tour-guide course (קורס מורי דרך) in the exact format the course coordinator uses — 50 questions, ~38 multiple-choice and ~12 short fill-in — and adds them to the practice-exam site. Use this skill whenever the user asks for a new practice exam, more exam questions, an exam on a new topic (נצרות, יהדות, תקופת הברזל, גבולות, ארכאולוגיה, גיאולוגיה, חי וצומח, תקופות שלטון, or any other course subject), a מבחן/מבחנים/שאלון/שאלות for the course, or wants existing exam questions reviewed, corrected or rebalanced. Also use it when the user pastes course material, a lecture recording transcript, a syllabus, a coordinator's emphases (דגשים) or a real past exam and wants questions generated from it. It covers the exam format, the question-writing rules that keep questions honest, and a validator that catches the defects these exams are prone to.
---

# Practice exams for the tour-guide course

The person using this is studying for the Israeli Ministry of Tourism guide
certification (קורס מורי דרך). They sit real exams written by their course
coordinator, and they practise on a static HTML site that holds the exams
built here. Questions that are wrong, ambiguous, or answerable without
knowing anything are worse than no questions at all — they teach the wrong
thing and waste the only commodity that matters before an exam, which is time.

So the job is not "produce 50 questions." It is "produce 50 questions that
each test one fact the student either knows or doesn't."

## The format

This mirrors the coordinator's real exams. Match it unless the user says otherwise.

| | |
|---|---|
| questions per exam | 50 |
| multiple choice | ~38 |
| fill-in (פתוחות) | ~12 |
| options per MC | exactly 4 |
| fill-in answer length | one word to three; never a sentence |
| scoring | 2 points per question, 100 total |
| conditions | sat in a classroom, closed book |

Fill-in questions are written as a statement with a blank, not as a question:
`"העיר דן מכונה במקרא גם בשם ___________________________"` → `ליש`.
The student writes a word or two, so the answer has to be a word or two.

Topics are split across the exam rather than grouped — the real exam moves
between subjects, and so should the practice. A four-topic exam divides
roughly 18/11/11/10; adjust to the subjects the user names.

Every question carries an explanation (`exp`). It is the only teaching the
student gets when they're wrong, so it must add something they didn't have:
the date, the distinction, the reason. See the rule on explanations below.

## Workflow

**1. Establish the subject matter.** Ask what the exam covers if it isn't
clear. If the user supplies material — a transcript, a syllabus, a past exam,
their own notes — work from that rather than from general knowledge, and keep
the coordinator's framing and terminology. `references/coordinator.md` has the
emphases he has already given; read it when the exam covers those subjects.

**2. Verify facts you are not certain of.** These exams have shipped errors
twice: a stream named `נחל שער` that does not exist (it is `נחל סער`), and a
date that came from a mis-heard recording. Transcripts are phonetic and the
course material is full of near-identical names — `תבליטי לכיש` against
`חרסי לכיש`, `עיבל` against `גריזים`, `722` against `720`. Search the web for
place names, people, dates and spellings you are reconstructing from audio or
memory. A wrong fact in a study aid is worse than a missing one.

**3. Write the exam as a Python generator, not as hand-edited HTML.** The
exams live inside one large `index.html` as JavaScript object literals. Editing
those by hand is how questions drift out of sync and how duplicates creep in.
Write a script that holds the questions as data and emits the JS, so the
questions can be regenerated, checked and corrected at the source.
`references/format.md` has the data shape, the site's structure, and how to
splice a new exam in.

**4. Run the validator before looking at the output.**

```bash
python3 .claude/skills/morey-derech-exam/scripts/check_exam.py exams.json
```

It catches the defects this material is prone to — unbalanced answer
positions, correct answers longer than their distractors, duplicate questions,
fill-ins that need a sentence, and questions that contain their own answer. It
is not a substitute for reading the questions, but it reliably catches what
the eye slides past. Fix what it reports in the generator and re-run.

**5. Check the exam in a browser.** Load the site, open the new exam, answer
through it. Past bugs — options rendering off-screen, a disabled button with
no explanation — were invisible in the data and obvious on screen.

**6. Ship it.** Commit, push, open a PR, merge.

## The rules that keep questions honest

These are not style preferences. Each one is here because a question that
broke it shipped and a student caught it.

### Exactly one option can be defended as correct

The failure is subtle: the answer you intend is right, but so is another one
under the literal wording.

> **Shipped broken:** *איזה מן החגים הבאים אינו מן התורה?*
> סוכות · חנוכה · פורים · פסח — marked חנוכה.
>
> Purim is not from the Torah either. It is from the Tanakh — Megillat Esther,
> in Ketuvim. Two correct answers.
>
> **Fixed:** the question now asks *אינו מן התנ״ך*, which only Hanukkah satisfies.

Read each distractor as a lawyer would and ask whether it also satisfies the
question as literally worded. Negative questions (`אינו`, `לא`, `אילו מהבאים
אינם`) are where this bites, because every distractor has to fail the predicate.
Watch for words that look interchangeable and are not: תורה / תנ״ך / מסורת,
מדאורייתא / מדרבנן, נביאים / כתובים.

### The question must not contain its own answer

> **Shipped broken:** *מי מבין הבאים חי מאוחר יותר?*
> רש״י (מאה 11) · הרמב״ם (מאה 12) · רבי יהודה הנשיא (מאה 2–3) · רב סעדיה גאון (מאה 10)
>
> You pick the largest number. No knowledge is tested. Eight questions had
> this shape.
>
> **Fixed:** the centuries are removed from the options and moved into the
> explanation, which now gives the full ordering.

Any ordering question — מי קדם, מה קרה ראשון, מי חי מאוחר יותר — must not print
dates in the options. The same applies to a correct answer that carries a
qualifier its distractors lack (`קודם (מאות 13–14)` among three bare options):
the extra specificity marks it even when the content doesn't.

### Distractors must be the same size and shape as the answer

A correct answer noticeably longer or more detailed than its distractors is
guessable from the silhouette. Keep the correct option within about 1.5× the
mean length of the others — the validator flags the rest. When a correct answer
genuinely needs more words, lengthen the distractors rather than trimming the
truth out of the answer.

Distractors also have to be *plausible and wrong*. An absurd option is a wasted
option: it narrows a four-way choice to three. Good distractors are the things
a half-prepared student actually confuses — the other Lachish find, the other
reformer king, the other valley in the Lower Galilee.

### Vary which position is correct

Shuffle the options per item with a seeded RNG so the exam is reproducible, and
check the distribution: no position should hold much more than a quarter of the
answers. Hand-written exams drift toward B and C.

### The explanation teaches; it does not restate

> **Shipped weak:** *מה מהבאים קרה ראשון?* → exp: "המוקדם מבין ארבעת האירועים."
>
> That tells the student nothing they couldn't see from the marked answer.
>
> **Rewritten:** "הסדר: אלכסנדר מוקדון 333 לפנה״ס ← חורבן בית שני 70 לספירה ←
> מרד בר כוכבא 132–135 ← הצלבנים בירושלים 1099."

When a fact is removed from the options to stop the question answering itself,
the explanation is where it goes. An explanation that names the distinction, the
date, or the trap is worth more than the question itself.

### Build traps the way the coordinator does, and say so

He repeatedly told the class the exam punishes skimming: *"שימו לב לכל מילה
בשאלה"*. He gave two of his own:

- `שמה של אחת מחמש ערי הפלישתים` — with `תל קסילה` among the options. It *is* a
  Philistine site. It is not one of the five cities.
- `בית ארבעת המרחבים הוא:` — one wrong option opens *"מבנה מתקופת המלוכה"*, which
  is true, and then goes wrong. The right answer is only visible if you read to
  the end.

Reproduce that shape deliberately, and use the explanation to name what the trap
was, so the student learns the habit and not just the fact.

## Reference files

- `references/format.md` — the data shape, the site layout, how to add an exam,
  and the validator's input format. Read before writing the generator.
- `references/coordinator.md` — the course's four exam subjects and the specific
  emphases and traps the coordinator has stated. Read when the exam covers them.
- `references/pitfalls.md` — the full catalogue of defects found in shipped
  exams, each with the broken version and the fix. Read when reviewing or
  correcting existing questions rather than writing new ones.
- `scripts/check_exam.py` — the validator. Run on every exam before shipping.
