# Defects found in shipped exams

Each of these reached the site and was caught by the student using it. They are
listed roughly in order of how much damage they do. Read this when reviewing or
correcting existing questions; when writing new ones, the summarised rules in
SKILL.md are enough.

---

## 1. Two defensible answers

**The shape:** the intended answer is correct, but a distractor also satisfies
the question as literally worded. Almost always in a negative question, because
there every distractor has to fail the predicate.

> *איזה מן החגים הבאים אינו מן התורה?*
> סוכות · חנוכה · פורים · פסח — marked חנוכה.

Purim is not from the Torah either. It is from the Tanakh — Megillat Esther, in
Ketuvim. The student spotted it: *"פורים הוא לא מהתורה אלא מהתנ״ך ועל כן לפי
השאלה גם פורים זו תשובה נכונה."*

**The fix:** the question asks `אינו מן התנ״ך`, which only Hanukkah satisfies.
The explanation now names all three tiers, because the distinction is itself
exam material:

> מן התורה: פסח, שבועות, סוכות, יום תרועה, יום כיפור · מן התנ״ך אך לא מן
> התורה: פורים · מן המסורת בלבד: חנוכה

**How to avoid it:** read each distractor as a lawyer would. Pairs that look
interchangeable and are not: תורה / תנ״ך / מסורת · מדאורייתא / מדרבנן ·
נביאים / כתובים · מקראי / מאוחר. The validator flags every negative question
for exactly this manual check.

---

## 2. The question answers itself

**The shape:** an ordering question that prints the dates in the options.

> *מי מבין הבאים חי מאוחר יותר?*
> רש״י (מאה 11) · הרמב״ם (מאה 12) · רבי יהודה הנשיא (מאה 2–3) · רב סעדיה גאון (מאה 10)

You pick the largest number. Nothing is tested. The student's reaction was the
right one: *"נראלך שזה אתגר להבין מי חי קודם?"*

**Eight questions** had this shape, across four different quizzes — it is a
systematic habit, not a slip, because writing the date feels like being helpful.

**The fix:** dates out of the options, into the explanation, and the explanation
upgraded from a restatement to the full ordering:

> הסדר: רבי יהודה הנשיא (מאה 2–3) ← רב סעדיה גאון (מאה 10) ← רש״י (מאה 11) ←
> הרמב״ם (מאה 12)

The validator detects this: an ordering question with dates in two or more
options is an error, not a warning.

---

## 3. Duplicate questions across exams

**The shape:** a family of exams built by hand, where nothing checks whether a
question already exists.

Measured on the shipped site: `TOPIC_EXAMS` holds **250 question slots and 124
distinct questions**. Exam 4 repeats 23 of exam 1's questions and 19 of exam
2's; exam 5 repeats 19 and 21. A student working through all five believes they
have done 250 questions and has really done about half that, with the repeats
rewarding recall of the practice rather than knowledge of the fact.

The generated family, `FOCUS_EXAMS`, holds **250 slots and 250 distinct
questions**, because the generator asserted uniqueness.

**How to avoid it:** write the exams as data in a generator, and run the
validator across the *whole corpus* including the existing exams, not just the
new file.

---

## 4. Factual errors from phonetic transcripts

**The shape:** material dictated from a recording, where a name is heard
slightly wrong and nothing checks it.

> **נחל שער** — shipped in three places. There is no such stream. It is
> **נחל סער**, with a samech, on the Hermon, draining into נחל חרמון (the
> Banias) and marking the boundary between the Golan and the Hermon.

The transcript was phonetic and ש/ס are indistinguishable in it. The same risk
sits on every name reconstructed from audio: תבליטי/חרסי לכיש, עיבל/גריזים,
722/720, רעמסס השני/השלישי.

**How to avoid it:** search the web for place names, people, dates and
spellings you are reconstructing from a recording or from memory. It costs one
lookup. A wrong fact in a study aid is worse than a missing one, because the
student memorises it.

A related case: the coordinator himself said *"אנדרטה של רעמסס השני שנלחם
בפלישתים"*. The Sea Peoples reliefs are **Ramesses III**, at Medinet Habu. When
his material is wrong, write the question around the uncontested part rather
than propagating the error, and say so.

---

## 5. The correct answer is marked by its shape

Three variants, all guessable without reading the content.

**Too long.** A correct answer much longer than its distractors stands out as a
silhouette. The gate is about 1.5× the mean distractor length. When the truth
genuinely needs more words, lengthen the distractors rather than trimming the
answer.

**Extra specificity.** Only the correct option carries a qualifier:

> *'ארבעה טורים' קדם או מאוחר יותר מ'שולחן ערוך'?*
> **קודם (מאות 13–14)** · מאוחר יותר · באותה מאה · אי אפשר לדעת

The parenthetical marks it, and doubles as a giveaway. Fixed to a bare `קודם`,
with the centuries moved into the explanation.

**Position drift.** Hand-written exams cluster the answer at B and C. Shuffle
per item with a seeded RNG and check the distribution; no position should hold
much more than a quarter.

---

## 6. Explanations that restate instead of teach

> *מה מהבאים קרה ראשון?* → exp: `המוקדם מבין ארבעת האירועים.`

The student already sees which option was marked. This adds nothing, and it is
the only feedback they get when they are wrong.

An explanation earns its place when it supplies the date, names the distinction,
or identifies the trap:

> תל קסילה הוא אתר פלישתי מובהק — אך לא אחת מחמש הערים. שימו לב לכל מילה בשאלה.

> אשורי, 701, נינוה. הרכז הזהיר במפורש מפני הבלבול בין תבליטי לכיש לחרסי לכיש.

---

## 7. Fill-ins that are really essay questions

The coordinator's rule is one word to three. An answer like
`קו 200 מ"מ המשקעים שעובר באזור בקעת באר שבע` cannot be marked consistently and
does not match what the real exam asks for. Ask for the term, and put the
elaboration in the explanation. The validator counts the words.

---

## 8. Interface defects that are invisible in the data

Worth remembering because the data looked perfect in all of these:

- Drag-and-drop slots rendered in a horizontal strip that clipped off-screen, so
  a student could not see there were slots left to fill — and the check button
  stayed disabled with no explanation. Reported by an older user via screenshot.
- Year ranges reversed by the bidi algorithm inside Hebrew text: `1522–1542`
  painted as `1542–1522`, in 27 places, including `724–722 לפנה"ס` reading as
  `722–724`. Fixed by isolating numeric ranges as LTR runs.
- A floating drag element that computed to `position: relative` because a
  later-declared class outranked it, so it laid out far from the cursor.

The lesson is narrow but firm: after changing anything the student interacts
with, open it in a browser at phone width and look at it. Assertions on the DOM
did not catch any of the three.
