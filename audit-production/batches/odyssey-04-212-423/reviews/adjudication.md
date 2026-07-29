# Adjudication Report

Reviewer 1 proposed no firm findings. Reviewer 2 proposed two explanatory-note findings, and both are sustained without modification. Note L335 falsely attributes the Book 17 recurrence of Menelaus' deer-and-lion simile to Odysseus; the recurrence is spoken by Telemachus as a quotation of Menelaus. Note L366 falsely includes the mortal princess Nausicaa in a chain of “divine women.” No proposal is rejected, modified, uncertain, or unresolved, and no formula-register-only issue is counted.

| ID | Lines | Category | Severity | Confidence | Decision | Finding | Greek evidence | Suggested direction |
|---|---|---|---|---:|---|---|---|---|
| O04-212-423-A-001 | note L335, with 4.335-340 and 17.118-131 | MISTRANSLATION | MINOR | 0.99 | R2-001 sustained | The note says the deer-and-lion simile is repeated “by Odysseus himself” at 17.126-131. In Book 17, Telemachus reports his visit to Sparta and quotes Menelaus' answer; Odysseus is the lion-like figure named inside the simile, not its speaker. | At 4.332-340, `ξανθὸς Μενέλαος` replies and delivers the simile. At 17.118-123, Telemachus narrates in the first person that Menelaus questioned him and then answered him, `καὶ τότε δή με ἔπεσσιν ἀμειβόμενος προσέειπεν`, before the repeated lines at 17.124-131. | Replace “by Odysseus himself” with “by Telemachus, when he quotes Menelaus' words,” or simply say that Telemachus later reports the simile. |
| O04-212-423-A-002 | note L366, with 4.365-382 and 6.15-17, 186-197 | MISTRANSLATION | MINOR | 0.98 | R2-002 sustained | The note calls Eidothea the first in a chain of “divine women” and includes Nausicaa in that chain. Nausicaa is a mortal Phaeacian princess, not a goddess, so the collective description misstates her narrative status. | Eidothea is explicitly divine at 4.382, `δῖα θεάων`. By contrast, Nausicaa is `θυγάτηρ μεγαλήτορος Ἀλκινόοιο` at 6.17 and identifies herself as Alcinous' daughter at 6.196; 6.16 says only that she resembles the immortals in form and beauty. | Use “female helpers,” or distinguish the divine helpers Eidothea, Calypso, and Ino from the mortal Nausicaa. |

## Proposal Dispositions

| Proposal | Decision | Reason |
|---|---|---|
| Reviewer 1 | No firm proposals | The sealed Reviewer 1 report contains zero firm finding IDs. |
| R2-001 | Sustained | The Book 17 speaker attribution is demonstrably false and materially misstates the recurrence's narrative transmission. |
| R2-002 | Sustained | Nausicaa's mortal genealogy is explicit, making the note's collective “divine women” label false. |
| None | Modified | Both Reviewer 2 proposals are sustained as submitted in category and severity. |
| None | Rejected | Every firm proposal produces a sustained finding. |
| None | Unresolved | No firm proposal remains uncertain or unresolved. |

Severity totals: CRITICAL 0; MAJOR 0; MODERATE 0; MINOR 2.

Sustained findings: 2.

Reviewer Jaccard agreement: 0% (`0` shared proposal keys divided by `2` distinct firm proposal keys in the union).

Findings per 100 records: 0.94.

Especially successful renderings:

- Lines 219-226 preserve the nepenthes drug's effects and the escalating family-death hypotheticals with clear scope and sequence.
- Lines 244-258 preserve Odysseus' self-disfigurement, disguise, evasion, sworn protection, intelligence gathering, killings, and return without losing agency.
- Lines 277-289 preserve Helen's three circuits of the horse, her vocal impersonation, Menelaus and Diomedes' impulse to respond, and Odysseus' restraint of Anticlus.

Calibration implications: both findings reinforce the existing `MISTRANSLATION`/`MINOR` treatment of localized false factual claims in explanatory notes. O04-212-423-A-001 adds an anchor for false attribution in a cross-book recurrence even when the repeated verse itself is accurate. O04-212-423-A-002 adds an anchor for a note that changes a character's mortal or divine status. Neither finding depends on fixed-register wording, so the automated formula lane is not duplicated.

```json
{
  "schema_version": 1,
  "batch_id": "odyssey-04-212-423",
  "record_count": 212,
  "unresolved_count": 0,
  "findings": [
    { "id": "O04-212-423-A-001", "severity": "MINOR", "category": "MISTRANSLATION" },
    { "id": "O04-212-423-A-002", "severity": "MINOR", "category": "MISTRANSLATION" }
  ],
  "reviewer_proposals": {
    "reviewer_1": [],
    "reviewer_2": [
      { "review_id": "R2-001", "proposal_key": "4.note-335-book17-speaker-attribution" },
      { "review_id": "R2-002", "proposal_key": "4.note-366-nausicaa-divine-status" }
    ]
  }
}
```
