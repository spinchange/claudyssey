# Adjudication Report

Reviewer 1 proposed two findings; Reviewer 2 proposed one. The shared note-383 proposal is sustained, and Reviewer 1's line 244-245 proposal is also sustained after checking the Greek context. No formula-only register findings are counted in this semantic adjudication.

| ID | Lines | Category | Severity | Confidence | Decision | Finding | Greek evidence | Suggested direction |
|---|---|---|---|---:|---|---|---|---|
| O02-218-434-A-001 | 244-245 | GRAMMAR | MODERATE | 0.86 | Sustained from R1-001 | "Men who outnumber you" makes Leocritus say that the suitors outnumber Mentor or the Ithacan people. In context he is answering Mentor's claim that the suitors are few and the people are many; the Greek says it would be hard even for more numerous men to fight the suitors over the feast. The English reverses the rhetorical force of the numerical comparison. | Mentor says `παύρους μνηστῆρας ... πολλοὶ ἐόντες` at 241. Leocritus replies `ἀργαλέον δὲ / ἀνδράσι καὶ πλεόνεσσι μαχήσασθαι περὶ δαιτί` at 244-245. | Revise toward "It is hard, even for more numerous men, to fight us over a feast." |
| O02-218-434-A-002 | note L383, with 383-387 | MISTRANSLATION | MODERATE | 0.85 | Sustained from R1-002 and R2-001 | The note says Athena borrows the ship "as herself." The Greek has just put her in Telemachus' likeness and then continues directly to her request to Noemon without a new disguise marker. The note therefore turns a disguised social action into an open divine action and misstates the mechanics by which Ithaca sees Telemachus taking command. | `Τηλεμάχῳ ἐικυῖα κατὰ πτόλιν ᾤχετο πάντῃ` at 383 is followed by `ἡ δʼ αὖτε ... Νοήμονα ... ᾔτεε νῆα θοήν` at 386-387. The next explicit new disguise is Mentor at 399-401. | Revise the note to say Athena recruits the crew and obtains the ship while continuing from Telemachus' likeness, then appears as Mentor to collect Telemachus. |

## Rejected And Unresolved Proposals

| Proposal | Decision | Reason |
|---|---|---|
| None | Not applicable | All firm reviewer proposals were sustained, with R1-002 and R2-001 merged as one shared finding. |

Severity totals: CRITICAL 0; MAJOR 0; MODERATE 2; MINOR 0.

Reviewer Jaccard agreement: 50%.

Findings per 100 records: 0.92.

Especially successful renderings:

- Lines 237-238: "they lay their own heads on the wager" preserves the self-risk in `σφὰς ... κεφαλὰς` while keeping the violent consumption of Odysseus' house.
- Lines 270-280: Athena's encouragement keeps the conditional pressure of inherited force, lineage, and Odyssean cunning.
- Line 409: "the sacred strength of Telemachus" preserves the marked epic elevation of `ἱερὴ ἲς Τηλεμάχοιο`.

Calibration implications: add line 244-245 as a `GRAMMAR` anchor for comparative-scope reversals, and note L383 as an explanatory-note `MISTRANSLATION` anchor for deity disguise mechanics.

```json
{
  "schema_version": 1,
  "batch_id": "odyssey-02-218-434",
  "record_count": 217,
  "unresolved_count": 0,
  "findings": [
    {
      "id": "O02-218-434-A-001",
      "severity": "MODERATE",
      "category": "GRAMMAR"
    },
    {
      "id": "O02-218-434-A-002",
      "severity": "MODERATE",
      "category": "MISTRANSLATION"
    }
  ],
  "reviewer_proposals": {
    "reviewer_1": [
      {
        "review_id": "R1-001",
        "proposal_key": "2.244-245-more-numerous-comparative-scope"
      },
      {
        "review_id": "R1-002",
        "proposal_key": "2.note-383-athena-disguise-noemon"
      }
    ],
    "reviewer_2": [
      {
        "review_id": "R2-001",
        "proposal_key": "2.note-383-athena-disguise-noemon"
      }
    ]
  }
}
```
