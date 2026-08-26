#!/usr/bin/env python3
"""Create word-aligned ASS/SRT captions for a complete Odyssey book."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import textwrap
from pathlib import Path

from faster_whisper import WhisperModel


ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "models" / "faster-whisper-tiny.en"
MAX_UNIT_CHARS = 108
WRAP_CHARS = 58
VISUAL_LEAD = 0.16
MANUAL_START_OVERRIDES = {
    # Whisper compressed several omitted words into one long token here.
    # The replacement is anchored to the measured pause immediately before
    # "and dropped it into the shrewd old woman's hands."
    # Shifted +3.00s on 2026-08-18: chunk-001 was regenerated to fix the
    # narrator saying "Odysseus" for "Aegisthus" (new take 213.60s vs 210.60s).
    "book-01": {336: 1414.55},
    # Whisper combined the source phrase "every one" into "everyone".
    # Anchor this cue just before that spoken word rather than at the next
    # directly matched word, "and".
    "book-02": {129: 540.62},
    # Proper names were recognized phonetically rather than matched to the
    # source spelling. Anchor these cues to the actual first spoken word.
    # Re-derived 2026-08-18 after regenerating chunk-001 (garbled "Odyssey"
    # title read; -1.200s) and chunk-004 (Aegisthus said as "Odysseus";
    # +11.784s). Cues 1 and 139 fall inside the new takes and were re-anchored
    # to the new spoken words; 102 shifts by -1.200s, 210/231 by +10.584s.
    "book-03": {
        # The deck ends just before narration begins at 7.80, leaving no room
        # for the normal visual lead without cutting off the title card.
        1: 7.78,
        102: 437.40,
        139: 602.54,
        210: 898.88,
        231: 992.26,
    },
    "book-04": {
        65: 278.88,
        135: 589.02,
    },
    "book-05": {
        96: 432.36,
        301: 1310.04,
        343: 1492.84,
    },
    "book-06": {
        12: 73.92,
        19: 104.47,
        88: 377.18,
    },
    "book-07": {
        44: 188.87,
        59: 245.93,
    },
    "book-08": {
        18: 84.44,
        26: 119.62,
        30: 139.84,
        82: 354.40,
        86: 373.88,
        96: 415.20,
        100: 430.32,
        103: 442.04,
        112: 478.34,
        161: 684.80,
        171: 731.28,
        189: 811.10,
        210: 892.68,
        338: 1405.14,
        355: 1469.40,
        436: 1813.62,
    },
    "book-09": {
        13: 57.28,
        16: 70.46,
        17: 76.86,
        84: 359.88,
        126: 547.46,
        156: 692.92,
        159: 711.00,
        178: 797.61,
        183: 819.13,
        188: 843.85,
        194: 863.95,
        202: 897.15,
        255: 1111.91,
        263: 1140.85,
        270: 1173.91,
        273: 1190.15,
        298: 1300.57,
        303: 1316.63,
        305: 1322.93,
        307: 1329.99,
        335: 1447.47,
        # The full-book pass compressed "were those you meant" into the same
        # long token as the preceding Cyclops taunt. A localized pass anchors
        # the next cue to the spoken "were".
        360: 1544.38,
        375: 1602.01,
        382: 1626.93,
        385: 1643.77,
        397: 1695.87,
        400: 1710.01,
        408: 1742.73,
    },
    "book-10": {
        # The full-book pass compressed "her house in order, daughters of
        # the springs" into one long "her" token. A localized pass places
        # "daughters" at 1121.76, including the standard 0.16-second lead.
        270: 1121.60,
    },
    "book-11": {
        # The second "not" is omitted; narration begins at "when."
        14: 64.30,
        33: 138.36,
        44: 190.75,
        47: 201.83,
        61: 256.87,
        72: 302.97,
        79: 330.29,
        107: 449.99,
        114: 470.33,
        120: 490.29,
        121: 496.93,
        129: 526.79,
        136: 551.15,
        144: 578.23,
        166: 671.13,
        171: 690.47,
        196: 796.03,
        202: 820.53,
        # "fastening a noose" was recognized phonetically as
        # "fascinating the news."
        217: 894.18,
        224: 920.43,
        234: 966.39,
        # The omitted opening is removed below; narration begins at "To."
        242: 1005.04,
        243: 1008.65,
        # The full pass compressed this complete opening into a long token.
        244: 1015.08,
        259: 1079.43,
        # The omitted opening is removed below; narration begins at
        # "Battle-cry."
        293: 1214.54,
        303: 1258.13,
        308: 1280.57,
        311: 1292.09,
        317: 1314.55,
        333: 1379.15,
        338: 1395.41,
        342: 1406.97,
        358: 1467.41,
        364: 1501.07,
        368: 1518.59,
        # The full pass compressed the complete opening before "rugged."
        369: 1522.12,
        376: 1550.29,
        390: 1600.97,
        395: 1620.63,
        # "unscarred" is omitted; narration begins at "never."
        412: 1692.11,
        421: 1735.81,
        426: 1751.41,
        442: 1827.30,
        464: 1916.83,
        475: 1964.37,
    },
    "book-12": {
        2: 12.40,
        17: 76.36,
        29: 126.00,
        67: 283.64,
        69: 295.58,
        82: 356.50,
        86: 370.20,
        116: 491.60,
        139: 590.10,
        147: 619.82,
        157: 669.58,
        # Localized passes recovered cue openings swallowed into long tokens.
        187: 802.50,
        194: 832.20,
        201: 868.78,
        207: 896.00,
        211: 908.82,
        215: 926.54,
        222: 955.92,
        231: 993.00,
        238: 1024.56,
        253: 1084.24,
        279: 1182.24,
        285: 1204.76,
        292: 1230.84,
    },
    "book-13": {
        23: 97.40,
        32: 132.30,
        34: 139.56,
        41: 165.76,
        47: 193.54,
        59: 252.44,
        60: 255.68,
        107: 445.88,
        117: 481.76,
        131: 533.84,
        133: 542.94,
        146: 586.88,
        152: 612.16,
        161: 644.24,
        194: 789.12,
        234: 958.76,
        240: 989.70,
        248: 1027.78,
    },
    "book-14": {
        15: 70.14,
        # Localized passes recover openings swallowed by long full-pass tokens.
        135: 546.88,
        162: 688.12,
        201: 853.98,
        290: 1236.38,
        332: 1403.96,
        334: 1413.64,
        # "Eumaeus" was compressed into a 1.56-second phonetic token.
        335: 1416.60,
        360: 1513.12,
        370: 1555.60,
        374: 1568.76,
        378: 1590.14,
        380: 1595.30,
    },
    "book-15": {
        11: 51.44,
        14: 63.84,
        40: 157.46,
        51: 203.72,
        54: 216.58,
        75: 305.12,
        117: 482.32,
        157: 642.98,
        162: 670.08,
        163: 674.10,
        191: 790.36,
        244: 1009.22,
        256: 1062.34,
        257: 1064.34,
        263: 1092.28,
        273: 1130.48,
        318: 1331.60,
        319: 1337.34,
        320: 1340.88,
        327: 1372.48,
        331: 1391.78,
        335: 1403.24,
        338: 1418.74,
        350: 1472.30,
        368: 1544.58,
        372: 1563.66,
        397: 1665.36,
        399: 1672.52,
        406: 1698.40,
        416: 1732.82,
        418: 1740.36,
    },
    "book-16": {
        6: 30.04,
        13: 63.82,
        32: 149.44,
        48: 213.26,
        70: 306.60,
        76: 331.12,
        85: 366.74,
        167: 718.28,
        208: 882.98,
        212: 899.58,
        240: 1032.48,
        265: 1135.58,
        266: 1138.78,
        274: 1171.20,
        279: 1192.86,
        307: 1314.44,
        310: 1324.56,
        332: 1417.38,
    },
    "book-17": {
        23: 106.20,
        31: 136.18,
        38: 158.44,
        44: 184.92,
        52: 214.70,
        58: 236.90,
        68: 275.28,
        90: 362.54,
        93: 371.62,
        123: 496.90,
        151: 608.96,
        177: 727.38,
        195: 807.10,
        228: 935.48,
        # A full-pass "and" token swallowed the opening of this cue.
        272: 1120.64,
        274: 1129.28,
        284: 1165.10,
        310: 1274.76,
        333: 1362.90,
        340: 1390.06,
        348: 1423.08,
        363: 1495.38,
        364: 1500.10,
        417: 1699.22,
        428: 1743.38,
        # A long "am" token compressed "afraid of this mob of hard suitors."
        430: 1753.52,
        452: 1830.22,
        453: 1832.86,
        455: 1842.86,
    },
    "book-18": {
        5: 22.70,
        44: 198.38,
        51: 231.60,
        74: 315.66,
        93: 395.50,
        95: 402.14,
        126: 529.72,
        136: 571.76,
        145: 613.74,
        181: 762.80,
        189: 795.28,
        194: 819.54,
        236: 988.32,
        244: 1023.40,
        266: 1099.74,
        283: 1162.26,
        301: 1232.34,
    },
    "book-19": {
        # The full pass compressed the quoted opening into a long token.
        11: 54.10,
        44: 181.32,
        77: 320.62,
        111: 462.64,
        140: 581.58,
        162: 657.12,
        240: 997.76,
        # The recording omits this cue's opening clause.
        252: 1045.26,
        281: 1158.18,
        310: 1283.36,
        332: 1378.70,
        # Original cue 350 is skipped below, so subsequent cue numbers shift.
        350: 1460.62,
        421: 1730.54,
        438: 1794.76,
        466: 1914.52,
    },
    "book-20": {
        14: 68.66,
        52: 238.06,
        77: 347.48,
        110: 482.46,
        140: 606.34,
        142: 617.16,
        154: 677.80,
        177: 765.96,
        185: 791.76,
        215: 929.98,
        222: 955.98,
        227: 975.10,
        229: 982.52,
        239: 1019.62,
        262: 1113.38,
        275: 1160.02,
        280: 1176.30,
        284: 1194.50,
        299: 1249.16,
    },
    "book-21": {
        11: 47.38,
        14: 58.50,
        15: 61.34,
        27: 112.64,
        49: 209.42,
        63: 269.90,
        103: 432.60,
        123: 514.92,
        124: 518.46,
        186: 761.04,
        189: 773.90,
        195: 799.78,
        219: 898.44,
        238: 980.96,
        253: 1036.74,
        258: 1056.80,
        274: 1125.04,
        325: 1334.44,
        333: 1363.34,
    },
    "book-22": {
        42: 162.62,
        50: 200.28,
        # "So he spoke" is absent; the recording begins at "And".
        55: 221.98,
        # A long full-pass token compressed the complete opening.
        95: 386.32,
        100: 407.34,
        121: 480.60,
        146: 580.24,
        188: 762.20,
        204: 833.30,
        217: 886.48,
        240: 981.10,
        257: 1046.38,
        261: 1065.12,
        314: 1298.74,
    },
    "book-23": {
        122: 485.04,
        184: 721.86,
        202: 798.76,
        278: 1136.98,
    },
    "book-24": {
        43: 173.18,
        50: 206.36,
        58: 244.68,
        78: 336.84,
        96: 410.52,
        205: 864.32,
        232: 965.12,
        344: 1409.14,
        408: 1668.26,
    },
}

# Cues whose entire wording was swallowed by a long Whisper token and
# therefore have no exact lexical match from which to derive a timestamp.
MANUAL_UNANCHORED_STARTS = {
    # After the 2026-08-18 chunk regenerations shifted this book +10.584s,
    # the fresh transcription emitted one 4.6-second "and" token swallowing
    # "and the other immortals, and then think of sleep..." This cue keeps
    # its old position shifted by the delta (1067.12 + 10.584).
    "book-03": {
        249: 1077.70,
    },
    # Whisper emitted one 5.32-second "the" token across the stable sequence
    # from "the mangers..." through "and leaned the...". This cue begins
    # between those two matched neighboring phrases.
    "book-04": {
        31: 136.74,
        # The next cue's repeated opening "and" was falsely matched to the
        # previous sentence; its first reliable spoken word is "chariot".
        32: 139.84,
    },
    # The full-book pass compressed the spoken final clause into two long
    # tokens. A localized word-timestamp pass anchors "is a companion..."
    # immediately after "brother".
    "book-08": {
        447: 1860.62,
    },
    # The full-book pass compressed the entire opening of Odysseus' taunt
    # into one 6.16-second token. A localized word-timestamp pass anchors
    # "Cyclops! Not so weak..." at its actual spoken start.
    "book-09": {
        359: 1541.08,
    },
    # The full pass compressed nineteen spoken source words across cues
    # 25–27 into one long token. A localized pass anchors cue 26.
    "book-21": {
        26: 110.26,
    },
}

# Source units absent from the finished narration. These must not be shown as
# captions because there is no corresponding speech in the audio.
MANUAL_SKIPPED_UNITS = {
    # The recording moves directly from "...sent bread along with them" to
    # "But the suitors..." and omits this source sentence.
    "book-04": {459},
    # The recording moves directly from "...stanch the black blood" to
    # "And Autolycus..." and omits this source cue in full.
    "book-19": {350},
}

# Source units that contain an omitted clause followed by narration that is
# present in the recording. Replace only the caption text that was not spoken.
MANUAL_UNIT_REPLACEMENTS = {
    # "And when we had come down to the ship and the sea" is omitted, but the
    # remainder of this source unit is narrated.
    "book-04": {
        419: "We made our supper, and ambrosial night came on,",
    },
    # "So he spoke" is omitted; the recording continues directly from
    # "suppliant" to "and at once".
    "book-05": {
        331: "And at once the god stayed his current, held back the wave,",
    },
    # "might sneer" is omitted; the recording continues directly from
    # "behind my back" to "there are insolent men".
    "book-06": {
        209: (
            "There are insolent men enough in the town; "
            "and one of the meaner sort, meeting us, might say:"
        ),
    },
    # "But when they had poured" is omitted; the narration continues directly
    # from "for the gods" to "and drunk what their hearts would have".
    "book-07": {
        143: (
            "And drunk what their hearts would have, "
            "Alcinous addressed them all, and said:"
        ),
    },
    "book-08": {
        # The narration moves directly from "Danaans alike" to "This the
        # famous singer sang."
        58: "on Trojans and Danaans alike.",
        # "nor does he lack the prime of youth" is omitted between "the great
        # strength" and "only he is broken by many evils."
        99: (
            "the thighs and calves of him, the two arms above, "
            "the massive neck, the great strength;"
        ),
        100: "only he is broken by many evils.",
        # The second "as" in "so much as see" is absent from the narration.
        206: (
            "and many hung down from above, from the roof-beam, "
            "fine as spider-webs, which no one could so much see —"
        ),
    },
    "book-09": {
        # "yet spent" is omitted; the narration moves directly from "was not"
        # to "from out our ships."
        118: "For the red wine was not from out our ships:",
        # The narration omits "he brought her against a headland" and
        # continues directly with the wind carrying the ship in.
        204: "and the wind carried her in from the sea.",
    },
    "book-10": {
        # The narration moves directly from "get us clear of the evil" to
        # "Gladly my ship fled" and omits the sea-tearing clause.
        96: "to fall to their oars and get us clear of the evil;",
        # The recording says "the gods call it" immediately after "like milk"
        # and omits the plant's name.
        234: (
            "The gods call it. And it is hard for mortal men "
            "to dig — but the gods have power to do all things."
        ),
        # The recording says "she swore it once" rather than "at once."
        267: "So I spoke, and she swore it once, as I demanded.",
        # The recording moves directly from "he followed" to "Meanwhile"
        # and omits the explanatory sentence.
        341: "he followed.",
    },
    "book-11": {
        # The recording omits the repeated "not" after "starry heaven."
        14: (
            "when he turns back from heaven to earth, "
            "but deadly night is stretched over wretched mortals."
        ),
        # The recording moves directly from "face" to the next sentence.
        111: "to look her own son in the face.",
        # The recording moves directly from "stood nine fathoms high" to
        # "To carry the din..." and omits the preceding clause.
        242: "To carry the din of furious war up into Olympus.",
        # The recording moves directly from "perished afterward" to
        # "Battle-cry and its groaning."
        293: "Battle-cry and its groaning",
        # The recording moves directly from "prize of honor" to "never
        # touched," omitting "unscarred."
        412: (
            "never touched by a thrown spear, never gashed in the close work, "
            "the way it happens so often"
        ),
    },
    "book-12": {
        # The recording moves from "hands from the cattle" directly to
        # "But when the companions had consumed..."
        245: (
            "As long as the men had bread and red wine, "
            "they kept their hands from the cattle:"
        ),
    },
    "book-13": {
        1: (
            "So he spoke; they were all hushed in silence, "
            "held fast under the spell, through the shadowy halls."
        ),
        26: (
            "his two wine-dark oxen have dragged the joint of plow "
            "through fallow ground,"
        ),
        117: (
            "That beautiful ship of the Phaeacians, coming home over "
            "the misted sea from her sending —"
        ),
        233: "in counsel and in words, and I am among all the gods",
        234: (
            "and famed for cunning and for profit. And yet you did not "
            "know Pallas Athena, daughter of Zeus — I who stand"
        ),
        330: "a good report by going there. He sits",
    },
    "book-14": {
        # The recording moves from "whether I have seen him" directly to
        # "I have wandered far."
        95: 'whether I have seen him. I have wandered far."',
        # The Zeus-of-Strangers clause is absent from the narration.
        294: 'And out of pity for yourself."',
        # The recording omits the interjection "yes."
        305: (
            '"Stranger — and a fine name I would win among mankind '
            "for goodness, now and ever after,"
        ),
    },
    "book-15": {
        157: (
            "where the old man will keep me in his house against my will, "
            'aching to host me. And I must get home quickly."'
        ),
        244: "I must — and hope someone will hand me a cup and a crust.",
        318: (
            "and everything is halved between them, and over both of them "
            "my father was the king —"
        ),
        350: (
            "When the hollow hull was freighted for their crossing, "
            "they sent a messenger up to bring the woman word."
        ),
        368: (
            "spoil for the seals and fishes, and I was left alone, "
            "my heart aching."
        ),
        416: (
            'and plenty for me — any man who met you would call you blessed."'
        ),
    },
    "book-16": {
        116: "bound them under his feet, and set off for the city.",
        117: (
            "Escape Athena, that Eumaeus the swineherd was gone "
            "from the farm:"
        ),
        166: (
            '"What ship was it, dear father, whose sailors brought '
            "you here to Ithaca?"
        ),
        208: "Lay it up in your heart.",
        225: "Then his shining son spoke out, answered him:",
        274: (
            "In counsel and in mind, and the people no longer "
            "look on us with any favor."
        ),
    },
    "book-18": {
        145: (
            "she cleansed her lovely face with the ambrosial balm "
            "that crowned Cytherea"
        ),
    },
    "book-19": {
        # The recording begins this cue at "Whether I stand out"; the
        # preceding question is absent.
        252: "Whether I stand out",
        # "Hermes" is absent between the two otherwise narrated clauses.
        306: (
            "in thievery and the oath: the god himself had given it him; "
            "to him he burned welcome thigh-pieces"
        ),
    },
    "book-21": {
        38: "With the case on her knees,",
    },
    "book-22": {
        55: (
            "And their knees went slack where they stood, "
            "and their hearts."
        ),
    },
    "book-23": {
        100: (
            "And we have killed the prop of the city — far the noblest "
            "of the young men in Ithaca."
        ),
        185: (
            "and not until too late that she laid to heart that folly,"
        ),
    },
    "book-24": {
        178: (
            '"Old man — no lack of skill in you at tending an orchard! '
            "Not one thing —"
        ),
        232: "And the heart in both of us hoped",
        384: (
            "and with them Laertes and Dolius got into armor too, "
            "gray though they were."
        ),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", default="book-01", help="Book id, for example book-01")
    parser.add_argument("--force-transcribe", action="store_true")
    return parser.parse_args()


def normalize_tokens(text: str) -> list[str]:
    text = text.replace("\\n", " ").replace("’", "'").lower()
    return [re.sub(r"[^a-z0-9']", "", token) for token in re.findall(r"[a-z0-9']+", text)]


def ass_time(seconds: float) -> str:
    centiseconds = round(seconds * 100)
    hours, remainder = divmod(centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    secs, centis = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def srt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def roman(number: int) -> str:
    values = [
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    output = []
    for value, symbol in values:
        while number >= value:
            output.append(symbol)
            number -= value
    return "".join(output)


def split_long_unit(text: str) -> list[str]:
    if len(text) <= MAX_UNIT_CHARS:
        return [text]
    pieces = re.split(r"(?<=[,;:—.!?])\s+", text)
    output: list[str] = []
    current = ""
    for piece in pieces:
        candidate = f"{current} {piece}".strip()
        if current and len(candidate) > MAX_UNIT_CHARS:
            output.append(current)
            current = piece
        else:
            current = candidate
    if current:
        output.append(current)

    final: list[str] = []
    for piece in output:
        if len(piece) <= MAX_UNIT_CHARS:
            final.append(piece)
        else:
            final.extend(
                textwrap.wrap(
                    piece,
                    width=MAX_UNIT_CHARS,
                    break_long_words=False,
                    break_on_hyphens=False,
                )
            )
    return final


def caption_units(paragraphs: list[str]) -> list[str]:
    units: list[str] = []
    for paragraph in paragraphs:
        if paragraph.strip() == "---":
            continue
        lines = [" ".join(line.split()) for line in paragraph.splitlines() if line.strip()]
        current = ""
        for line in lines:
            candidate = f"{current} {line}".strip()
            closes_thought = bool(re.search(r"""[.!?:]["']?$""", current))
            if current and (len(candidate) > MAX_UNIT_CHARS or closes_thought):
                units.extend(split_long_unit(current))
                current = line
            else:
                current = candidate
        if current:
            units.extend(split_long_unit(current))
    return units


def wrap_caption(text: str) -> str:
    if len(text) <= WRAP_CHARS:
        return text

    words = text.split()
    candidates: list[tuple[float, str, str]] = []
    for split_at in range(1, len(words)):
        left = " ".join(words[:split_at])
        right = " ".join(words[split_at:])
        if len(left) > 66 or len(right) > 66:
            continue
        punctuation_bonus = 14 if re.search(r"""[,;:—.!?]["']?$""", left) else 0
        score = abs(len(left) - len(right)) - punctuation_bonus
        candidates.append((score, left, right))
    if not candidates:
        raise RuntimeError(f"Caption cannot be balanced into two lines: {text!r}")
    _, left, right = min(candidates, key=lambda candidate: candidate[0])
    return f"{left}\\n{right}"


def transcribe(audio: Path, output: Path) -> dict:
    model = WhisperModel(
        "tiny.en",
        device="cpu",
        compute_type="int8",
        download_root=str(MODEL_ROOT),
    )
    segments, info = model.transcribe(
        str(audio),
        language="en",
        beam_size=5,
        word_timestamps=True,
        vad_filter=False,
        condition_on_previous_text=True,
    )
    words = []
    transcript = []
    for segment in segments:
        transcript.append(segment.text.strip())
        for word in segment.words or []:
            words.append(
                {
                    "word": word.word.strip(),
                    "start": round(word.start, 3),
                    "end": round(word.end, 3),
                    "probability": round(word.probability, 5),
                }
            )
    payload = {
        "audio": str(audio.relative_to(ROOT)),
        "duration": round(info.duration, 3),
        "language": info.language,
        "language_probability": info.language_probability,
        "transcript": " ".join(transcript),
        "words": words,
    }
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def probe_audio_duration(audio: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(audio),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return round(float(result.stdout.strip()), 3)


def align_units(
    units: list[str],
    word_data: dict,
    manual_unanchored_starts: dict[int, float] | None = None,
) -> tuple[list[dict], dict]:
    source_words: list[str] = []
    unit_ranges: list[tuple[int, int]] = []
    for unit in units:
        start = len(source_words)
        source_words.extend(normalize_tokens(unit))
        unit_ranges.append((start, len(source_words)))

    recognized = word_data["words"]
    recognized_words = [
        normalize_tokens(word["word"])[0] if normalize_tokens(word["word"]) else ""
        for word in recognized
    ]
    matcher = difflib.SequenceMatcher(None, source_words, recognized_words, autojunk=False)
    source_to_recognized: dict[int, int] = {}
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            source_to_recognized[block.a + offset] = block.b + offset

    starts: list[float] = []
    anchor_details: list[dict] = []
    for index, (start, end) in enumerate(unit_ranges):
        cue_number = index + 1
        if manual_unanchored_starts and cue_number in manual_unanchored_starts:
            cue_start = round(float(manual_unanchored_starts[cue_number]), 3)
            starts.append(cue_start)
            anchor_details.append(
                {
                    "cue": cue_number,
                    "recognized_word": "[manual timestamp]",
                    "recognized_start": cue_start,
                    "missing_prefix_words": len(normalize_tokens(units[index])),
                    "cue_start": cue_start,
                }
            )
            continue
        candidates = [
            (source_index, source_to_recognized[source_index])
            for source_index in range(start, end)
            if source_index in source_to_recognized
        ]
        if not candidates:
            raise RuntimeError(f"No word timestamp anchor for caption {cue_number}: {units[index]}")
        source_index, recognized_index = candidates[0]
        word = recognized[recognized_index]
        missing_prefix = source_index - start
        estimated_start = float(word["start"]) - (0.20 * missing_prefix) - VISUAL_LEAD
        starts.append(round(max(0.0, estimated_start), 3))
        anchor_details.append(
            {
                "cue": index + 1,
                "recognized_word": word["word"],
                "recognized_start": word["start"],
                "missing_prefix_words": missing_prefix,
                "cue_start": starts[-1],
            }
        )

    for index in range(1, len(starts)):
        if starts[index] <= starts[index - 1]:
            raise RuntimeError(
                f"Non-increasing alignment at captions {index} and {index + 1}: "
                f"{starts[index - 1]} >= {starts[index]}"
            )

    cues = []
    for index, unit in enumerate(units):
        start = starts[index]
        end = starts[index + 1] if index + 1 < len(starts) else float(word_data["duration"])
        cues.append(
            {
                "start": start,
                "end": round(end, 3),
                "text": wrap_caption(unit),
            }
        )

    matched = len(source_to_recognized)
    stats = {
        "source_words": len(source_words),
        "matched_source_words": matched,
        "match_ratio": matched / len(source_words),
        "recognized_words": len(recognized),
        "anchor_details": anchor_details,
    }
    return cues, stats


def write_ass(
    output: Path,
    title: str,
    deck: str,
    header: str,
    duration: float,
    narration_cues: list[dict],
) -> None:
    ass_header = f"""[Script Info]
Title: {title} — Living Manuscript Edition
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Georgia,74,&H006AB3D7,&H006AB3D7,&HCC130D08,&H80000000,0,0,0,0,100,100,7,0,1,3,2,5,120,120,0,1
Style: Deck,Georgia,35,&H00C7DDE8,&H00C7DDE8,&HCC130D08,&H80000000,0,1,0,0,100,100,1,0,1,2.5,1,5,210,210,0,1
Style: Header,Georgia,23,&H005594B8,&H005594B8,&H80130D08,&H00000000,0,0,0,0,100,100,3,0,1,1.5,0,8,80,80,54,1
Style: Narration,Georgia,49,&H00D8E7EE,&H00D8E7EE,&HE0130D08,&H70000000,0,0,0,0,100,100,0.4,0,1,3,1,2,170,170,185,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    first_start = narration_cues[0]["start"]
    events = [
        f"Dialogue: 0,{ass_time(0)},{ass_time(first_start)},Title,,0,0,0,,"
        rf"{{\pos(960,445)\fad(600,500)\bord3\blur0.5}}{title}",
        f"Dialogue: 0,{ass_time(0)},{ass_time(first_start)},Deck,,0,0,0,,"
        rf"{{\pos(960,565)\fad(600,500)}}{deck.replace(chr(10), r'\N')}",
        f"Dialogue: 0,{ass_time(first_start)},{ass_time(duration)},Header,,0,0,0,,"
        rf"{{\fad(800,500)}}{header}",
    ]
    for cue in narration_cues:
        events.append(
            f"Dialogue: 1,{ass_time(cue['start'])},{ass_time(cue['end'])},"
            f"Narration,,0,0,0,,{{\\fad(60,120)}}{cue['text'].replace(chr(92) + 'n', r'\N')}"
        )
    output.write_text(ass_header + "\n".join(events) + "\n", encoding="utf-8-sig")


def write_srt(output: Path, cues: list[dict]) -> None:
    blocks = []
    for index, cue in enumerate(cues, start=1):
        text = cue["text"].replace("\\n", "\n")
        blocks.append(
            f"{index}\n{srt_time(cue['start'])} --> {srt_time(cue['end'])}\n{text}\n"
        )
    output.write_text("\n".join(blocks), encoding="utf-8")


def main() -> None:
    args = parse_args()
    book_number = int(args.book.split("-")[-1])
    roman_book = roman(book_number)

    audio = ROOT / "books" / f"{args.book}.mp3"
    source = ROOT / "clean" / f"{args.book}.txt"
    words_output = ROOT / "captions" / f"{args.book}-words.json"
    cues_output = ROOT / "captions" / f"{args.book}-cues.json"
    ass_output = ROOT / "captions" / f"{args.book}.ass"
    srt_output = ROOT / "captions" / f"{args.book}.srt"
    report_output = ROOT / "captions" / f"{args.book}-alignment.txt"

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\r?\n\s*\r?\n", source.read_text(encoding="utf-8-sig").strip())
        if paragraph.strip()
    ]
    if len(paragraphs) < 3:
        raise RuntimeError(f"Unexpected source structure in {source}")

    title = f"ODYSSEY — BOOK {roman_book}"
    deck = "\n".join(" ".join(line.split()) for line in paragraphs[1].splitlines())
    deck = deck.replace("; ", ";\n", 1)
    units = caption_units(paragraphs[2:])
    skipped_units = MANUAL_SKIPPED_UNITS.get(args.book, set())
    if skipped_units:
        units = [
            unit
            for cue_number, unit in enumerate(units, start=1)
            if cue_number not in skipped_units
        ]
    for cue_number, replacement in MANUAL_UNIT_REPLACEMENTS.get(args.book, {}).items():
        units[cue_number - 1] = replacement

    if args.force_transcribe or not words_output.exists():
        print(f"Transcribing {audio.relative_to(ROOT)} with word timestamps...")
        word_data = transcribe(audio, words_output)
    else:
        print(f"Reusing {words_output.relative_to(ROOT)}")
        word_data = json.loads(words_output.read_text(encoding="utf-8"))
    word_data["duration"] = probe_audio_duration(audio)

    narration_cues, stats = align_units(
        units,
        word_data,
        MANUAL_UNANCHORED_STARTS.get(args.book),
    )
    for cue_number, start in MANUAL_START_OVERRIDES.get(args.book, {}).items():
        cue_index = cue_number - 1
        narration_cues[cue_index]["start"] = start
        if cue_index > 0:
            narration_cues[cue_index - 1]["end"] = start
    duration = float(word_data["duration"])
    all_cues = [
        {"start": 0.0, "end": narration_cues[0]["start"], "kind": "title", "text": title},
        {"start": 0.0, "end": narration_cues[0]["start"], "kind": "deck", "text": deck.replace("\n", "\\n")},
        *narration_cues,
    ]
    cues_output.write_text(
        json.dumps(
            {
                "book": args.book,
                "duration": duration,
                "visual_lead": VISUAL_LEAD,
                "cues": all_cues,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    header = f"HOMER’S ODYSSEY  ·  BOOK {roman_book}"
    write_ass(ass_output, title, deck, header, duration, narration_cues)
    write_srt(srt_output, narration_cues)

    report_lines = [
        f"{title} full-book caption alignment",
        f"Duration: {duration:.3f}s",
        f"Narration cues: {len(narration_cues)}",
        f"Source words: {stats['source_words']}",
        f"Directly matched source words: {stats['matched_source_words']} "
        f"({stats['match_ratio']:.1%})",
        f"Recognized words: {stats['recognized_words']}",
        f"Visual lead: {VISUAL_LEAD:.2f}s",
        "",
        "Cue | Start | Anchor | Missing prefix | Caption",
    ]
    for cue, anchor in zip(narration_cues, stats["anchor_details"]):
        report_lines.append(
            f"{anchor['cue']:>3} | {cue['start']:>8.3f} | "
            f"{anchor['recognized_word']:<18} | {anchor['missing_prefix_words']:>14} | "
            f"{cue['text'].replace('\\n', ' / ')}"
        )
    report_output.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Wrote {cues_output.relative_to(ROOT)}")
    print(f"Wrote {ass_output.relative_to(ROOT)}")
    print(f"Wrote {srt_output.relative_to(ROOT)}")
    print(f"Wrote {report_output.relative_to(ROOT)}")
    print(
        f"{len(narration_cues)} cues; matched "
        f"{stats['matched_source_words']}/{stats['source_words']} source words "
        f"({stats['match_ratio']:.1%})"
    )


if __name__ == "__main__":
    main()
