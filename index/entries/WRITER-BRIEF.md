# Phase 3 writer brief — how to write index entries

You are one of several writers producing the Odyssey name index in parallel. You
own **one worklist** (`_worklist-NN.md`) and write entries for **only** its
headwords. Every headword in the poem belongs to exactly one worklist, so stay in
your lane: do not add, drop, rename, or reorder headwords, and do not touch any
file but your own output.

## Read first (in this order)

1. **`index/canon.md`** — the editorial spine. You MUST use:
   - the **Entry schema** and the seven **style-contract rules**;
   - the **alias-resolution table** (resolve every "also called" per this table;
     for context-dependent ones like "son of Atreus" or "Mentor", state the rule,
     don't guess);
   - the **genealogy skeletons** (draw parentage from here or the text only).
2. **`index/entries/entries-A.md`** — five gold-standard entries
   (Aegisthus, Agamemnon, Alcinous, Antinous, Athena). Match their format, voice,
   and density exactly. When in doubt, imitate these.
3. **`FORMULAS.md`** — the authoritative epithet register. Quote epithets from
   here **verbatim** (English + Greek). If a name has no epithet here, omit the
   *Epithets* field — do not invent one.

## The entry format (from canon.md — restated)

```
**Headword** (Greek Ἑλληνικά) · CATEGORY
One to three sentences: who/what, the family or place it belongs to, and why it
matters to the poem. Present tense for narrative events.
*Epithets:* fixed English rendering (Greek, first-ref) — only if in FORMULAS.md.
*Also called:* aliases / patronymics / disguises, resolved per canon.md.
*Kin:* parentage and key relations, from the genealogy skeletons or the text.
**Refs:** curated book.line citations — first appearance + pivotal scenes.
*See also:* related headwords.
```

- The **Greek** in the headword line: use the standard spelling (see the gold
  entries and FORMULAS.md). If you are not confident of the polytonic form, give
  the headword without it rather than guessing accents.
- Fields in *italics* are optional — include one only when it applies.

## Rules

1. **Length scales with importance.** Use the `hits` count in your worklist as the
   guide: major figures (roughly 40+ hits, or any of the named gods, the suitors'
   leaders, the main mortals) get ~40–90 words; walk-ons (a genealogical father, a
   named rower, a heroine glimpsed in the underworld) get ~15–30. Do not pad a
   minor name into a major entry.
2. **Citations: use only the refs in your worklist.** They are real and verified.
   Curate — for a major name pick ≤ ~8 meaningful refs (first appearance, key
   scenes) and add "…and throughout"; for a minor name list its handful in full.
   **Never write a book.line that is not in your worklist's ref list.**
3. **Verify a scene before you pin it to a line.** If you assert that a specific
   event happens *at* a specific line (e.g. "blinded at 9.383"), open
   `translation/book-NN.md` (zero-padded: 9 → `book-09.md`) and confirm that line
   says what you claim. Vague "…and throughout" needs no check; a specific claim
   does.
4. **Resolve aliases per canon.md**, never by invention. Context-dependent aliases
   get the rule stated ("Menelaus in the Telemachy, Agamemnon in the
   underworld"), not a blind pick.
5. **Genealogy from the skeletons or the text only.** Do not import parentage from
   later mythographers without marking it "(later tradition)".
6. **Voice = the footnote apparatus.** Scholarly, plain, unfussy; the register of
   the `[^L…]` notes and the gold entries. No breathless summary, no second person.
7. **Spellings are the translation's** familiar Latinate forms; use the headword
   exactly as your worklist gives it.

## Special cases you may hit

- **`Phaeacian_rowers`** — this is one folded headword covering the young
  Phaeacians named only as they line up for the Book 8 games. Write a **single**
  entry titled *The Phaeacian competitors* (or similar), listing the names, ~20–30
  words. Don't try to give each rower a line.
- **"several men" notes** (e.g. Polybus, Antiphates, Castor) — the note tells you
  the surface name hides more than one person. Write one entry that distinguishes
  them in a clause each.
- **Argus (OTHER)** — the hit-count conflates the hound with the giant in Hermes's
  epithet "slayer of Argus." Your entry is the **hound** (Book 17); cite only the
  Book-17 refs and note that "slayer of Argus" is a different Argus (see Hermes).

## Output

- Write **only** the entries, in worklist order, separated by a line containing
  just `---`, to the output file your worklist names (`entries-NN.md`).
- **No preamble, no title, no closing commentary** — the file is entries only,
  ready to concatenate with the other slices.
- One entry per headword. Skip nothing.
