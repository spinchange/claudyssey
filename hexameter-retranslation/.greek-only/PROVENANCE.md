# Books 13–24 Greek-First Retranslation: Staging Record

Status: **review drafts only**. The existing `book-13.md` through `book-24.md` files and all performance files have not been replaced or regenerated.

## Method

- Books 13–24 were newly translated into this `.greek-only` directory.
- The Greek files in `../greek/` were the semantic source for authoring. Translators were explicitly prohibited from reading the existing prose translations, the existing hexameter versions, performance files, and earlier authoring artifacts.
- Each book was then independently checked line by line by a reviewer who had not authored that book. Reviewers used the Greek source and the staged draft, not the existing English versions.
- One disputed lemma at 15.150, `δεδισκόμενος`, was checked lexically and retained in the greeting/toasting sense.
- Only after translation and cross-review were complete were the staged drafts compared mechanically with the two older English versions. That comparison was diagnostic only; it was not used to revise the wording.

## Assignment and independent review

| Workstream | First-pass books | Cross-reviewed books |
|---|---|---|
| A | 13, 16, 19, 22 | 14, 17, 20, 23 |
| B | 14, 17, 20, 23 | 15, 18, 21, 24 |
| C | 15, 18, 21, 24 | 13, 16, 19, 22 |

## Structural validation

All twelve files pass `python .greek-only/validate.py 13 14 15 16 17 18 19 20 21 22 23 24`.

| Book | Retained Greek IDs | Staged IDs | Result |
|---:|---:|---:|---|
| 13 | 440 | 440 | PASS |
| 14 | 533 | 533 | PASS |
| 15 | 557 | 557 | PASS |
| 16 | 480 | 480 | PASS |
| 17 | 606 | 606 | PASS |
| 18 | 428 | 428 | PASS |
| 19 | 604 | 604 | PASS |
| 20 | 394 | 394 | PASS |
| 21 | 434 | 434 | PASS |
| 22 | 501 | 501 | PASS |
| 23 | 371 | 371 | PASS |
| 24 | 548 | 548 | PASS |
| **Total** | **5,896** | **5,896** | **PASS** |

The validator confirms exact source-ID order, nonempty verse bodies, and dialogue typography. Its remaining repeated-line notices are review warnings for Homeric formulas, not structural failures.

Source irregularities deliberately preserved:

- Book 14 source order is 62, 64, 63, 65.
- Book 16 source omits ID 101.
- Book 23 source omits ID 49.

## Post hoc overlap diagnostic

The percentage below is the share of each staged draft's unique contiguous five-word sequences also found in the named older English file. Formulaic and ordinary English account for some unavoidable matches.

| Book | Existing prose | Existing hexameter |
|---:|---:|---:|
| 13 | 1.91% | 3.57% |
| 14 | 1.57% | 2.86% |
| 15 | 2.07% | 3.54% |
| 16 | 1.79% | 3.72% |
| 17 | 1.98% | 3.70% |
| 18 | 1.83% | 3.41% |
| 19 | 1.34% | 2.74% |
| 20 | 2.16% | 2.92% |
| 21 | 1.88% | 3.27% |
| 22 | 1.75% | 3.49% |
| 23 | 2.57% | 4.27% |
| 24 | 1.94% | 3.35% |
| **Weighted total** | **1.87%** | **3.38%** |

## Readings retained for later editorial review

- 15.206: `ἐξαίνυτο`, rendered contextually as unloading/placing the gifts into the stern.
- 22.304: lexically compressed; conservatively rendered “cowering under the cloudbanks.”
- 23.281: `ἐξ ἁλός`, retained as “from the sea,” though “away from the sea” is possible.
- 24.182: elliptical `σφι`, made explicit as Odysseus' companions from the following plural attackers.
- 24.497: compressed roster syntax, rendered as four men including Odysseus.

## SHA-256 record

| Book | Greek source | Staged draft |
|---:|---|---|
| 13 | `be481c2851769235d3c9937af00100bf8a254159096573b805c82d7e3dd32a3d` | `e9ffd041ca8db82257261cca122de1452e6596ff951e01213f0221a6ec5581fd` |
| 14 | `bd51d01b99fd85dd5b70845d275cd8bc3d4c425b0352b5457121edd2ee4f07b4` | `80a3b0b9d4f6873196181244c040998ebea7afd6e9d6cd8aa4c13e1ca50250f6` |
| 15 | `6152310d68cd3231ac44c9d87a515f085ddbfebe0c0054fa20f546f67b9a73e9` | `f027b60f22789fd8e56d3be91b4d347292cf37985fa1c7594c8ec82b9f5f3b7c` |
| 16 | `9a5e20c6811adba63245a2c86f91ced021d82d9dcf42710297577ba8847387ad` | `10c2bcaa98e839fc9f0cfcb8b3f8a4d947c518ffbb6b440b662ffcaca404b5e1` |
| 17 | `625f090f4abf09e85adff24ce65846f50602c35329d4f707fe93d694fda2af48` | `2d59730686d6505ac56ccd753f3c7c62b082c1e79b7557caa36514ff5314eab6` |
| 18 | `b049f17e79b35c2844ced69597afcb042b6573bfa5f91a0a94a1275e77b40103` | `e293fd2a08b11d6579e9440dd44c4f750e2df3b568de4c77763f15469034a97a` |
| 19 | `fc09def09471e84c00fc460a5a7d282dd9bcaa5014ce4da84e1a32c1c4435144` | `0065243e0028b68e499ea261ed5088cc9af6b7de9b075a44b7bcf0684c9420f6` |
| 20 | `ed567f3dba75117d8e77e0546c9cfd01ca0305b0547ff53d8819e67c0facc2de` | `7f003bc72624bf5c2b6712af07e44684e161ccc1e1f193bb074db22a061dd826` |
| 21 | `863aad57f93d79346f750c41885557ac2447ff62ef424f4ed0c178afd3006be1` | `bc4fe874f25d71bb364d63d9d65b2c66e1a25d32349e59c5fa4fd6d6d31784d0` |
| 22 | `d5119e0c95721dacf5497b39ca4c7723a13d89ad1fb75b7f249fcd406f7cfdbb` | `b18242d551004ecaa0bbea2dfcada0d3ce9ada7fc8bf70b3b1751fc1402ab74d` |
| 23 | `5b424d3c25d2a7bddd4bfc31da204c53b8e2915fb458468598958e81755dcd59` | `74cf171ed3a0d02b1079f40fef78175a5592d4217d0263ed9c106fd9ee1c87f0` |
| 24 | `3dd64e79572be20bc2b6ca7ae4dae1363a961d66df378d9397355d56694f91b1` | `05f0cac17b6801fae1c0db00f969ead69e4cf26d4af581c6319e870fb858cf06` |
