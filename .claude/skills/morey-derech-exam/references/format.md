# Format, data shape, and how to add an exam to the site

## Where the exams live

Everything is one self-contained file: `index.html` in the repo root. No build
step, no dependencies — it is served straight from GitHub Pages. Inside it,
near the bottom, are three JavaScript object literals:

| constant | what it holds | shape |
|---|---|---|
| `EXAMS` | the oldest "classic" exams | 24 MC + 6 open questions, scored 60 |
| `TOPIC_EXAMS` | topic exams 1–5 | 50 items each, mixed mc/fill |
| `FOCUS_EXAMS` | the coordinator-emphasis exams 6–10 | 50 items each, mixed mc/fill |

`TOPIC_EXAMS` and `FOCUS_EXAMS` share one rendering engine. `FOCUS_EXAMS` is
merged into `TOPIC_EXAMS` at load:

```js
Object.assign(TOPIC_EXAMS, FOCUS_EXAMS);
```

so any new family only has to match the `TOPIC_EXAMS` item shape and be merged
the same way — `renderTopicExam`, `computeTopicScore` and `renderTopicResults`
then handle it with no changes. Keys must not collide; the existing families
use 1–5 and 6–10.

`renderSelect()` draws the exam picker. Each family gets its own section with a
heading, a sub-line, and one button per exam. Add a new section there.

## Item shape

```js
// multiple choice
{ type: "mc", topic: "תקופת הברזל – ארכאולוגיה וכתובות",
  q: "היכן נמצאו תבליטי לכיש?",
  options: ["...", "...", "...", "..."],   // exactly 4
  correct: 2,                               // 0-based index into options
  exp: "אשורי, 701, נינוה. לא לבלבל עם חרסי לכיש." }

// fill-in
{ type: "fill", topic: "תקופת הברזל – ארכאולוגיה וכתובות",
  q: "העיר דן מכונה במקרא גם בשם ___________________________",
  answer: "ליש",
  exp: "שבט דן נדד בכללותו צפונה וכבש את ליש." }
```

`topic` drives the per-subject score breakdown on the results screen. The
renderer buckets on the text before `" – "` (space, en-dash, space), so
`"יהדות – חגים וצומות"` and `"יהדות – ספרות ההלכה"` both score under `יהדות`.
Keep the separator exact or the breakdown silently splits into extra buckets.

The blank in a fill question is a literal run of underscores in the string. The
input box is separate; the underscores are just the visual gap.

## Writing the generator

Hold the questions as Python data and emit the JS. This is not ceremony — the
hand-maintained `TOPIC_EXAMS` family ended up with 250 question slots holding
only 124 distinct questions, because nothing was checking. The generated family
has 250 of 250 distinct.

A generator that has worked well:

```python
def mc(topic, q, correct, distractors, exp):
    return {"_t": "mc", "topic": topic, "q": q,
            "correct_text": correct, "distractors": list(distractors), "exp": exp}

def fill(topic, q, answer, exp):
    return {"_t": "fill", "topic": topic, "q": q, "answer": answer, "exp": exp}
```

Writing the correct answer as `correct_text` rather than an index means you
never have to track which slot it landed in. Shuffle per item with a seeded RNG
and look the index up afterwards:

```python
rng = random.Random(SEED)          # seeded, so a rebuild is reproducible
opts = [it["correct_text"]] + it["distractors"]
rng.shuffle(opts)
correct = opts.index(it["correct_text"])
```

Emit two things: the `.js` to splice into `index.html`, and a `.json` in the
validator's shape so `check_exam.py` can read it.

## Validator input

```json
{
  "exam_key": {
    "title": "מבחן ...",
    "items": [ { "type": "mc", "topic": "...", "q": "...",
                 "options": ["..."], "correct": 0, "exp": "..." } ]
  }
}
```

```bash
python3 .claude/skills/morey-derech-exam/scripts/check_exam.py exams.json
python3 .../check_exam.py exams.json --items 0        # skip the 50-item check
python3 .../check_exam.py exams.json --strict         # fail on warnings too
```

Feed it **all** the exams on the site, not just the new ones — duplicate
detection only works across the whole corpus, and a new exam that repeats an
old question is the easiest mistake to make.

## Splicing into index.html

Replace the whole constant rather than patching inside it, so the file always
matches the generator:

```python
start = html.index("const FOCUS_EXAMS = {")
end   = html.index("const TOPIC_EXAMS = {")     # the next constant
html  = html[:start] + new_js + "\n" + html[end:]
```

Then check the result parses before committing — a broken literal takes the
whole site down, and there is no build step to catch it:

```python
m = re.search(r'<script>\n(.*)\n</script>', html, re.S)
open('/tmp/check.js','w').write(m.group(1))
```
```bash
node --check /tmp/check.js
```

## Verifying in a browser

Serve the directory and drive it with Playwright — Chromium is at
`/opt/pw-browsers/chromium-*/chrome-linux/chrome`, launch with `--no-sandbox`,
and run node with `NODE_PATH=/opt/node22/lib/node_modules`.

Worth asserting, because each of these has broken before: the exam renders 50
cards; every MC marks its correct option and opens its explanation; every
fill-in reveals its answer; the score and the per-topic breakdown compute; no
horizontal overflow at 390px; no console errors. Screenshot it at phone width
and actually look — a disabled button with no explanation and options rendering
off-screen were both invisible in the data.
