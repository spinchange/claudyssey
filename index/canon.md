# Name index — Phase 2 canonicalization

This is the editorial spine of the index. Phase 1 (`tools/build_index.py`) found
*every capitalized token* and where it occurs, mechanically and without judgment.
This document supplies the judgment: it decides which tokens are real names, what
each name's canonical headword is, which other names and epithets resolve to it,
and how the families connect. Phase 3 (the entry-writers) consume this file plus
`occurrences.json`; they resolve aliases and assign genealogy **from here**, never
by independent guesswork, so that eight parallel writers can't contradict one
another.

Coverage note: this seed fixes the schema, the category buckets, and — fully —
every *ambiguous or aliased* name (the hard cases that must be centralized). The
unambiguous long tail (~200 singleton place/person names that need no alias
resolution) is extended into the tables below before Phase 3 fans out; each such
name is a mechanical lift from `occurrences.json` and carries no cross-entry risk.

---

## Category buckets

Every headword is tagged with exactly one:

- **MORTAL** — human beings (Odysseus, Nestor, the suitors, slaves, the dead).
- **GOD** — Olympians, and lesser divine/supernatural beings (nymphs, Cyclopes,
  Sirens, the winds when personified, personified Dawn/Sleep/Rumor).
- **PEOPLE** — collective ethnonyms (Achaeans, Phaeacians, Cicones).
- **PLACE** — lands, cities, islands, rivers, the underworld.
- **OTHER** — named animals (Argus the dog), objects, and personifications that
  don't sit cleanly as gods.

---

## Entry schema (the style contract for Phase 3)

Each entry is written to this shape. Fields in *(parentheses)* are omitted when
they don't apply.

> **Headword** (Greek Ἑλληνικά) · CATEGORY
> One to three sentences: who or what this is, the family or place it belongs to,
> and why it matters to the poem — its decisive action or role. Present tense for
> events in the narrative.
> *(Epithets:* the fixed English renderings, quoted verbatim from `FORMULAS.md`,
> each with its Greek.*)*
> *(Also called:* aliases, patronymics, and disguises used in the text, each
> cross-linked to its own entry.*)*
> *(Kin:* parentage and key relations, drawn from the genealogy section below or
> stated in the text.*)*
> **Refs:** curated key citations `book.line` — first appearance and pivotal
> scenes — then book coverage. Not an exhaustive dump.
> *(See also:* related entries.*)*

Rules for writers:

1. **Voice matches the footnote apparatus** — scholarly, plain, unfussy; the same
   register as the `[^L…]` notes in `translation/`. No breathless summary.
2. **Spellings are the translation's** — familiar Latinate forms (Achilles, not
   Akhilleus; Circe, not Kirke). Use the headword exactly as this file fixes it.
3. **Epithets are quoted, not invented** — take the English from `FORMULAS.md`.
   If a name has no fixed epithet there, omit the field.
4. **Aliases resolve per the table below** — never invent a cross-reference; if a
   token is genuinely ambiguous (e.g. "son of Atreus"), say so and give the rule.
5. **Genealogy comes from the text or this file** — do not import parentage from
   later mythographers (Apollodorus, etc.) without marking it "(later tradition)".
6. **Citations come from `occurrences.json`** — real `book.line` refs only. Curate
   to ≤ ~8 key refs for a major name and add "…and throughout"; give the full
   short list for a minor one.
7. **Length scales with importance** — ~40–90 words for a major figure, ~15–30 for
   a walk-on. The index is a finding aid, not a set of essays.

---

## Alias-resolution table (the load-bearing part)

The Odyssey names people by patronymic, epithet, and disguise far more than by
plain name. This table maps every such surface form **as it appears in this
translation** to its canonical headword. A reader who meets the phrase in the
left column and is lost looks it up here.

### One-to-one aliases (always the same person/thing)

| As it appears in the text | Canonical headword | Note |
|---|---|---|
| Pallas; Pallas Athena | **Athena** | cult title, always Athena |
| gray-eyed goddess; daughter of Zeus (in Athena scenes) | **Athena** | γλαυκῶπις |
| the slayer of Argus; sharp-eyed / strong / guide slayer of Argus | **Hermes** | ἀργεϊφόντης; Argus here is the giant watchman, *not* the dog |
| son of Cronos; Cronos' son | **Zeus** | Κρονίων; "Cronos" *alone* = the Titan father |
| Zeus who gathers the clouds; Zeus of the wide voice; aegis-bearing Zeus | **Zeus** | fixed epithets |
| the earth-shaker; shaker of earth; who holds the earth | **Poseidon** | ἐνοσίχθων / γαιήοχος |
| daughter of Atlas; the Concealer | **Calypso** | καλύπτειν = "to conceal" |
| laughter-loving | **Aphrodite** | φιλομμειδής |
| Gerenian horseman | **Nestor** | fixed epithet |
| Nobody | **Odysseus** | the trick-name Οὖτις given to Polyphemus (Book 9) |
| the Cyclops (singular, in Book 9) | **Polyphemus** | the *plural* Cyclopes = the race |
| Helios Hyperion; Hyperion (as the Sun) | **Helios** | compound name of the Sun-god |

### Context-dependent (resolve by scene — flag, don't guess)

| As it appears | Could be | Rule |
|---|---|---|
| son of Atreus; Atreus' son; Atreides | **Agamemnon** *or* **Menelaus** | both are sons of Atreus; the scene decides — Menelaus in the Telemachy (Books 3–4, 15), Agamemnon in the underworld and paradigm-of-the-bad-homecoming passages |
| Mentor | **Athena** *or* the mortal **Mentor** | Athena wears his shape (2.268ff, 22.206ff, 24.503ff); but Mentor is also a real Ithacan, Odysseus's steward, addressing the assembly as himself at 2.225ff |
| Old Man of the Sea | **Proteus** (Book 4) | γέρων ἅλιος; in this poem the phrase is Proteus, whom Menelaus wrestles off Egypt |
| the Old Man | context | Laertes, Nestor, Aegyptius, or the disguised Odysseus, per scene |

### Collective names for the Greeks (all three = the Achaean host)

| Ethnonym | Note |
|---|---|
| **Achaeans** | the poem's default name for the Greeks (also *Achaean* sg.) |
| **Argives** | from Argos; interchangeable with Achaeans for the whole host |
| **Danaans** | third synonym, metrically convenient; same referent |

### Same place, two names

| Names | Canonical | Note |
|---|---|---|
| Troy; Ilium | **Troy** | the city; *Ilium* (Ἴλιος) is the same place |
| Argos (the region); Argos (Odysseus's dog) | split | the Peloponnesian place vs. **Argus** the hound (Book 17) — keep as two entries; note the collision |
| Scheria; land of the Phaeacians | **Scheria** | the Phaeacians' island, Odysseus's last stop before Ithaca |

---

## Genealogy skeletons

Compact family trees for the houses the poem keeps returning to. Entry-writers
draw the **Kin** field from these; anything here is attested in the text unless
marked "(later tradition)".

**House of Odysseus (Ithaca).**
Arceisius → **Laertes** (m. **Anticleia**, daughter of **Autolycus**) →
**Odysseus** (m. **Penelope**, daughter of **Icarius**) → **Telemachus**.

**House of Atreus (Mycenae/Sparta).**
**Atreus** → **Agamemnon** (m. **Clytemnestra** → **Orestes**) and **Menelaus**
(m. **Helen** → Hermione). **Aegisthus** (son of Thyestes, Atreus's brother)
seduces Clytemnestra, kills Agamemnon at his homecoming, and is killed by Orestes
— the poem's recurring cautionary parallel to Odysseus's own return.

**Pylos.**
**Neleus** → **Nestor** → sons incl. **Peisistratus** (Telemachus's companion),
Antilochus (dead at Troy), Thrasymedes.

**Scheria (the Phaeacians).**
**Poseidon** (+ Periboea) → **Nausithous** → **Rhexenor** and **Alcinous**.
Rhexenor's daughter **Arete** marries her uncle **Alcinous**; their children
include **Nausicaa** and **Laodamas**.

**Divine (as the poem uses them).**
**Cronos** → **Zeus**, **Poseidon**, **Hades**, **Hera**. Zeus's children in the
poem include **Athena**, **Apollo**, **Artemis**, **Hermes**, **Aphrodite** (here
daughter of Zeus and Dione), **Ares**. **Atlas** → **Calypso**. **Helios** (the
Sun) fathers **Circe** and Aeetes; **Helios** + Neaera → the nymphs who herd his
cattle (Book 12).

---

## Master registry (full coverage)

The complete registry now lives in **[`registry.md`](registry.md)** — **433 headwords**,
generated by `tools/build_registry.py` from a curated classification joined against
`occurrences.json`, so hit-counts and book coverage stay true to the text. The
alias-resolution and genealogy sections above are the editorial judgment that feeds
it; the generator also reports every unclassified token, so coverage is auditable.

Breakdown: Mortals 237 · Gods & divine beings 55 · Peoples & groups 32 ·
Places 101 · Animals/objects/sky 8.

The registry is the **work list for Phase 3**: one entry per headword, sliced
alphabetically across the Sonnet writers. Five headwords already have hand-written
gold-standard entries in [`entries-A.md`](entries-A.md) — Aegisthus, Agamemnon,
Alcinous, Antinous, Athena — which fix the format every other entry follows.

To regenerate after any edit to the classification or the translation:

```powershell
python tools\build_index.py      # Phase 1: refresh occurrences.{json,md}
python tools\build_registry.py   # Phase 2: refresh registry.md + coverage audit
```
