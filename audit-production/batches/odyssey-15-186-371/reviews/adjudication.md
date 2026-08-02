# Adjudication Report

Reviewer 1 proposed two findings and Reviewer 2 proposed one. The two proposals about Theoclymenus' supplication identify the same issue and are merged. Two distinct findings are sustained: one localized epithet displacement and one consequential reversal of social agency. No fixed-wording-only formula deviation is counted.

| ID | Lines | Category | Severity | Confidence | Decision | Finding | Greek evidence | Suggested direction |
|---|---|---|---|---:|---|---|---|---|
| O15-186-371-A-001 | 15.233-234 | LEXICAL | MINOR | 0.91 | R1-001 sustained | “The Fury who strikes the house” replaces the epithet's explicit frightfulness with a specific action directed at a house. “Fury” retains part of the dread, but the invented domestic target changes the compressed characterization. | `θεὰ δασπλῆτις Ἐρινύς` means “the dreadful/frightful goddess Erinys”; `δασπλῆτις` does not denote striking a house. | Use “the dreadful Fury” or “the frightful goddess Erinys,” without supplying a house as the object of a blow. |
| O15-186-371-A-002 | 15.277-278 | GRAMMAR | MODERATE | 0.99 | R1-002 and R2-001 sustained and merged | “Since in my flight I have found you / begging” naturally makes Telemachus the person found begging and adds an act of finding. Theoclymenus says that he himself, while fleeing, supplicated Telemachus. His earlier “I beg you” preserves the general posture but does not repair this explicit local reversal. | In `ἐπεί σε φυγὼν ἱκέτευσα`, first-person `ἱκέτευσα` has Theoclymenus supplicate second-person `σε`, Telemachus; participle `φυγών` also describes Theoclymenus. | Keep Theoclymenus as agent: “since in my flight I came to you as a suppliant; / do not let them kill me.” |

## Proposal Decisions

| Reviewer proposal | Decision | Result | Category | Severity | Confidence | Reason |
|---|---|---|---|---|---:|---|
| R1-001 | Sustained | O15-186-371-A-001 | LEXICAL | MINOR | 0.91 | `δασπλῆτις` characterizes Erinys as dreadful or frightful; it does not assign her a house-striking action. |
| R1-002 | Sustained; merged with R2-001 | O15-186-371-A-002 | GRAMMAR | MODERATE | 0.99 | First-person `ἱκέτευσα` makes Theoclymenus the suppliant and `σε` makes Telemachus the person supplicated. |
| R2-001 | Sustained; merged with R1-002 | O15-186-371-A-002 | GRAMMAR | MODERATE | 0.99 | The English syntax reverses the appeal's roles and obscures why Telemachus should receive the fugitive. |

Rejected proposals: none.

Modified proposals: none. The duplicate pair is merged without substantive modification.

Uncertain or unresolved proposals: none.

Severity totals: CRITICAL 0; MAJOR 0; MODERATE 1; MINOR 1.

Sustained findings: 2.

Reviewer Jaccard agreement: 50% (`1` shared proposal key among `2` distinct keys).

Findings per 100 records: 1.08.

## Especially Successful Renderings

- **15.195-220:** Telemachus' tactful request, Peisistratus' comic assessment of Nestor, and the companions' rapid embarkation preserve their speech relations and pacing.
- **15.245-255:** The compressed Amphiaraus, Cleitus, and Polypheides genealogy remains clear while retaining divine love, fatal bribery, Dawn's abduction, and prophetic succession.
- **15.301-345:** Odysseus' test and service-skills catalogue preserve the disguised king's strategy, Eumaeus' alarm, and the thematic link between service, hunger, and wandering.

## Calibration Implications

Dense genealogical epithets remain auditable when an unsupported concrete action replaces their characterization, though preserved dread can keep severity minor. Explicit person marking must control supplication and social agency even when nearby language preserves the scene's general posture. No registered recurrence here produces a distinct semantic formula finding.

```json
{
  "schema_version": 1,
  "batch_id": "odyssey-15-186-371",
  "record_count": 186,
  "unresolved_count": 0,
  "findings": [
    {"id": "O15-186-371-A-001", "severity": "MINOR", "category": "LEXICAL"},
    {"id": "O15-186-371-A-002", "severity": "MODERATE", "category": "GRAMMAR"}
  ],
  "reviewer_proposals": {
    "reviewer_1": [
      {"review_id": "R1-001", "proposal_key": "15.233-234-daspletis-replaced-house-striking"},
      {"review_id": "R1-002", "proposal_key": "15.277-278-supplication-agency-reversed"}
    ],
    "reviewer_2": [
      {"review_id": "R2-001", "proposal_key": "15.277-278-supplication-agency-reversed"}
    ]
  }
}
```
