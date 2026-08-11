# Seeding the /api/ corpus — drafts and sequence

*Drafts only; nothing here has been posted. Every draft discloses the AI
authorship in the first sentence or two, on the theory (borne out by the
independence-page comment history) that these communities punish discovery
far harder than disclosure. Claims are scoped to what the independence page
supports. Fill in the Hugging Face URL after upload.*

## Sequence

1. **Upload the Hugging Face dataset** (folder is built at `hf-dataset/`):

   ```powershell
   pip install -U huggingface_hub
   hf auth login
   hf upload spinchange/claudyssey-odyssey hf-dataset --repo-type dataset
   ```

   (Repo id is yours to choose; drafts below assume
   `spinchange/claudyssey-odyssey`.)

2. **Link it back**: add the HF link to the /api/ landing page ("Mirrored as
   a Hugging Face dataset: ...") and to the README, so each channel
   corroborates the other. One-line edit in `tools/build_web.py`, rebuild.

3. **Post r/datasets** (best single audience-fit; low effort, durable via
   search).

4. **Mail the lists**: Digital Classicist and the Liverpool Classicists
   list accept announcements of digital resources; Humanist takes
   announcements too. One email, lightly adapted per list. Check each
   list's current submission address before sending; they change.

5. **Optional, separate decision: Show HN.** Bigger blast radius, invites
   the remix fight on a day of your choosing. The independence page should
   be the second link in the text, not buried.

6. **Tell Perseus** (courtesy + possible listing): their digitization is in
   the Greek fields with attribution retained; projects built on
   canonical-greekLit have occasionally been listed by them. Short note via
   their contact form or the canonical-greekLit repo discussions.

---

## r/datasets post

**Title:**

> Homer's Odyssey as a Greek-English parallel corpus: all 12,107 lines
> aligned one-to-one, English is CC0 (AI-translated, human-edited, with a
> published independence analysis)

**Body:**

The Odyssey, aligned line by line: one JSON object per verse line with the
Greek (Murray 1919, via Perseus) and an English translation keyed to the
same line numbering, plus a 434-entry index of every named person, god,
people, and place with full line citations.

- Hugging Face: https://huggingface.co/datasets/spinchange/claudyssey-odyssey
- Static files, no key or rate limit: https://theclaudyssey.com/api/
- Row shape: `{"book": 9, "line": 366, "greek": "Οὖτις ἐμοί γʼ ὄνομα· Οὖτιν δέ με κικλήσκουσι", "en": "Nobody is my name. Nobody is what they call me —"}`

Provenance, stated up front: the English was produced by a language model
(Claude) translating from the Greek line by line, then edited by a human.
Because "the model just remixed Fagles" is the obvious objection, we
measured it instead of arguing it: n-gram overlap and shared-passage
analysis against nine translations (Pope to Green), all human-vs-human
pairs as controls, method and code published. Short version: no evidence
of construction by extensive verbatim reuse, and the tests' limits are
stated on the page. https://theclaudyssey.com/independence.html

Licensing is per-field: the English is CC0 (public domain, any use); the
Greek text is public domain, its Perseus digitization CC BY-SA 4.0; the
name index is CC BY 4.0.

Why it might be useful: the existing public-domain English Odysseys
(Butler, Palmer, Pope...) don't align to the Greek lineation, and the
modern line-aware translations are under copyright. As far as we know this
is the only complete English Odyssey that is both line-aligned to the
standard Greek numbering and free to reuse. If you know a prior one, I
want to hear about it.

---

## Mailing-list email (Digital Classicist / Liverpool Classicists / Humanist)

**Subject:** A CC0 line-aligned English Odyssey, with parallel-text data
keyed to the vulgate numbering

Dear list,

I'd like to announce an openly licensed resource that may be useful for
teaching and for digital work on Homer.

The Claudyssey (https://theclaudyssey.com) is a complete English
translation of the Odyssey with one English line per Greek line, keyed to
the standard (Murray 1919) numbering, including its transposed pairs and
athetized omissions. The translation was produced by a large language
model working from the Perseus digitization of Murray's text, and edited
by me; I state this plainly because the provenance is the interesting
part, and because the obvious question (is it a re-synthesis of prior
translations?) is addressed by a published, reproducible overlap analysis
against nine translations rather than by assertion:
https://theclaudyssey.com/independence.html

The English is dedicated to the public domain (CC0); there is no
permission to seek for coursepacks, apps, or derived editions. Alongside
the reading edition there is a machine-readable layer at
https://theclaudyssey.com/api/ : the full Greek-English parallel corpus as
JSONL (12,107 aligned lines), the translation source with its 1,260
line-keyed notes (CC BY), and a JSON index of all named entities with
their citations. The same corpus is on Hugging Face:
https://huggingface.co/datasets/spinchange/claudyssey-odyssey

Corrections are welcome and are applied in public; the full revision
history is at https://github.com/spinchange/claudyssey

With best wishes,
Chris Duffy

*(Per-list tweaks: Digital Classicist and Liverpool Classicists: send as
is. Humanist: add one sentence of framing for the general-DH reader, e.g.
"Beyond classics, the corpus may interest anyone working on alignment,
literary MT, or evaluation of language models against checkable
sources.")*

---

## Show HN (optional, separate decision)

**Title:** Show HN: The Odyssey, translated line-for-line by an LLM, CC0,
with the Greek aligned as data

**URL:** https://theclaudyssey.com/api/ (the api page, not the homepage:
HN respects an artifact over a pitch)

**First comment (post immediately after submitting):**

Producer here. The short version: a complete English Odyssey, one line per
Greek line on the standard numbering, public domain (CC0), with the
Greek-English pairs served as JSONL and mirrored on Hugging Face.

The predictable objection is that an LLM translation is a remix of the
translations in its training data. We took that seriously enough to
measure: n-gram and shared-passage overlap against nine translations from
Pope to Green, with all 36 human-vs-human pairs as controls and a
synthetic-splice positive control, code public. What the tests support
and what they can't rule out is on one page:
https://theclaudyssey.com/independence.html

Also happy to answer questions about the process: every line was verified
one-to-one against the Greek, the poem's repeated formulas render
identically at each recurrence by rule, and the 188 corrections from the
whole-poem audit are in the git history.

---

## Perseus note (courtesy)

**Subject:** Your Odyssey digitization, in a CC0 aligned translation

Dear Perseus team,

A brief note of thanks. The Claudyssey (https://theclaudyssey.com) is a
complete line-for-line English translation of the Odyssey built on your
digitization of Murray's text (tlg0012.tlg002.perseus-grc2); the CC BY-SA
attribution travels with the Greek in the repository and in the parallel
corpus we serve (https://theclaudyssey.com/api/). The English is CC0. The
translation was produced by a language model and human-edited, with a
published analysis of its independence from prior translations. If it is
ever useful to you or worth listing among projects built on
canonical-greekLit, it is yours to use; either way, thank you for making
this kind of work possible.

Chris Duffy

---

## Claim-scoping notes (for review before anything is posted)

- "As far as we know this is the only complete English Odyssey that is
  both line-aligned and free to reuse": scoped with "as far as we know"
  and an explicit invitation to falsify. Cowper is verse but not aligned
  to the Greek lineation; Butler/Palmer are prose; Murray's own facing
  translation is prose. If someone produces a counterexample, thank them
  and edit the claim everywhere it appears.
- The independence summary in every draft is the approved bounded form
  (no evidence of extensive verbatim reuse + limits stated), never
  "proven original."
- Nothing anywhere mentions the pending Wilson row or its predictions.
- The r/datasets title says "AI-translated" before the license, so nobody
  can feel ambushed in the comments.
- Numbers used (12,107 lines; 434 entries; 1,260 notes; nine
  translations; 188 corrections) are all verified against the built
  manifest/registry as of 2026-08-10.
