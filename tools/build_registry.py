"""Phase 2, master registry: the curated classification of every real name.

Phase 1 (build_index.py) extracted every capitalized token mechanically. This
file supplies the editorial judgment Phase 1 can't: which tokens are real names,
each name's canonical headword and category, which inflectional variants and
alias-forms fold into it, and a one-line disambiguating note where the same
surface form hides several people.

The classification lives in REGISTRY below, as data. This script joins it against
`index/occurrences.json` to aggregate hit-counts and book coverage, then writes
`index/registry.md`. It also prints every occurrence token that is NOT classified
(the function-word / line-initial noise, plus anything a curator missed), so
coverage is auditable — nothing is dropped silently.

Categories: MORTAL, GOD, PEOPLE, PLACE, OTHER (see canon.md).

Usage:  python tools/build_registry.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

# Polytonic Greek and combining diacritics must survive a legacy Windows console.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent
OCC = ROOT / "index" / "occurrences.json"
OUT = ROOT / "index" / "registry.md"


def E(headword, cat, tokens=None, aliases="", note=""):
    return {
        "headword": headword,
        "cat": cat,
        "tokens": tokens if tokens is not None else [headword],
        "aliases": aliases,
        "note": note,
    }


# ---------------------------------------------------------------------------
# The curated registry. Every entry is an editorial decision. `tokens` lists the
# occurrence.json keys whose counts roll up into this headword (inflected forms,
# folded aliases). `aliases` records other names/epithets used for the figure;
# `note` disambiguates or places them.
# ---------------------------------------------------------------------------
REGISTRY = [
    # ===================== GODS & divine / supernatural =====================
    E("Zeus", "GOD", ["Zeus"], "son of Cronos; cloud-gatherer; Zeus of the wide voice; aegis-bearing",
      "father of gods and men; the poem's guarantor of xenia and of the plot"),
    E("Athena", "GOD", ["Athena", "Pallas", "Tritogeneia"], "Pallas; gray-eyed Athena; disguises: Mentes, Mentor",
      "Odysseus's patron; the intelligence behind the whole action"),
    E("Poseidon", "GOD", ["Poseidon"], "the earth-shaker; who holds the earth; blue-haired",
      "Odysseus's divine antagonist, enraged for the blinded Polyphemus"),
    E("Apollo", "GOD", ["Apollo", "Phoebus"], "Phoebus; of the silver bow",
      "archer-god; the suitors die on his festival day"),
    E("Hermes", "GOD", ["Hermes"], "the slayer of Argus (Argeiphontes); the guide",
      "messenger; frees Odysseus from Calypso and gives him the moly"),
    E("Artemis", "GOD", ["Artemis"], "of the golden shafts", "archer-goddess; sender of gentle death to women"),
    E("Aphrodite", "GOD", ["Aphrodite", "Cytherea"], "laughter-loving; Cytherea",
      "caught with Ares in Hephaestus's net in Demodocus's song"),
    E("Ares", "GOD", ["Ares"], "", "war-god; Aphrodite's lover in the song of Book 8"),
    E("Hephaestus", "GOD", ["Hephaestus"], "the famous god of the two strong arms; of the many designs",
      "smith-god; snares Ares and Aphrodite"),
    E("Hera", "GOD", ["Hera"], "", "wife of Zeus"),
    E("Hades", "GOD", ["Hades"], "", "lord of the dead; by metonymy his house = the underworld"),
    E("Persephone", "GOD", ["Persephone"], "dread Persephone", "queen of the dead; marshals the heroines' ghosts"),
    E("Calypso", "GOD", ["Calypso"], "daughter of Atlas; the Concealer; shining among goddesses",
      "the nymph who holds Odysseus seven years on Ogygia"),
    E("Circe", "GOD", ["Circe"], "of the lovely braids; the dread goddess",
      "witch-goddess of Aeaea, daughter of Helios; turns the crew to swine"),
    E("Helios", "GOD", ["Helios", "Hyperion", "Sun"], "Helios Hyperion; the Sun",
      "the Sun; his cattle, eaten on Thrinacia, doom the crew"),
    E("Proteus", "GOD", ["Proteus"], "the Old Man of the Sea", "shape-shifting sea-god Menelaus pins off Egypt"),
    E("Ino", "GOD", ["Ino"], "Leucothea, the White Goddess", "sea-goddess who gives Odysseus her veil in the storm"),
    E("Thetis", "GOD", ["Thetis"], "", "sea-goddess, mother of Achilles"),
    E("Amphitrite", "GOD", ["Amphitrite"], "", "the sea personified; wife of Poseidon"),
    E("Eidothea", "GOD", ["Eidothea"], "", "sea-nymph, Proteus's daughter, who coaches Menelaus"),
    E("Thoosa", "GOD", ["Thoösa"], "", "sea-nymph, mother of Polyphemus by Poseidon"),
    E("Phorcys", "GOD", ["Phorcys"], "old man of the sea", "sea-god; a harbor of Ithaca bears his name"),
    E("Leto", "GOD", ["Leto"], "", "mother of Apollo and Artemis"),
    E("Demeter", "GOD", ["Demeter"], "", "grain-goddess; loved Iasion"),
    E("Dionysus", "GOD", ["Dionysus"], "", "gave Ariadne's golden urn; witness against her"),
    E("Themis", "GOD", ["Themis"], "", "goddess who convenes and dissolves assemblies"),
    E("Hebe", "GOD", ["Hebe"], "", "youth-goddess, wife of the deified Heracles"),
    E("Eileithyia", "GOD", ["Eileithyia"], "", "goddess of childbirth"),
    E("Paeeon", "GOD", ["Paeeon"], "", "physician of the gods"),
    E("Rumor", "GOD", ["Rumor"], "Ossa", "the divine messenger-voice that rouses Ithaca"),
    E("Earth", "GOD", ["Earth"], "Gaia", "invoked with Heaven and Styx in the gods' great oath"),
    E("Muses", "GOD", ["Muse", "Muses"], "", "goddesses of song, invoked in the proem and at Achilles's funeral"),
    E("Graces", "GOD", ["Graces"], "the Charites", "attendants of Aphrodite"),
    E("Furies", "GOD", ["Furies"], "the Erinyes", "avengers of oaths, parents, and beggars"),
    E("Spinners", "GOD", ["Spinners"], "Klothes; the Fates", "the spinners of a man's fated thread"),
    E("Naiads", "GOD", ["Naiads", "Nymphs"], "the Nymphs", "the water-nymphs of the Ithacan cave of Phorcys"),
    E("Maia", "GOD", ["Maia"], "", "nymph, mother of Hermes"),
    E("Perse", "GOD", ["Perse"], "", "Oceanid, mother of Circe and Aeetes by Helios"),
    E("Neaera", "GOD", ["Neaera"], "", "nymph, mother of Helios's herdswomen"),
    E("Lampetie", "GOD", ["Lampetie"], "", "nymph who guards Helios's cattle; sister of Phaethusa"),
    E("Phaethusa", "GOD", ["Phaethusa"], "", "nymph who guards Helios's cattle"),
    E("Polyphemus", "GOD", ["Polyphemus", "Cyclops"], "the Cyclops",
      "the one-eyed son of Poseidon whom Odysseus blinds in Book 9"),
    E("Cyclopes", "GOD", ["Cyclopes"], "", "the lawless one-eyed race; Polyphemus is one of them"),
    E("Scylla", "GOD", ["Scylla"], "", "the six-headed cliff-monster, child of Crataiis"),
    E("Charybdis", "GOD", ["Charybdis"], "", "the devouring whirlpool paired with Scylla"),
    E("Sirens", "GOD", ["Sirens"], "", "the singers whose song kills; Odysseus hears them bound"),
    E("Gorgon", "GOD", ["Gorgon"], "", "the monstrous head Odysseus fears Persephone will send up"),
    E("Crataiis", "GOD", ["Crataiis"], "", "mother of Scylla"),
    E("Aeolus", "GOD", ["Aeolus", "Aeolian", "Hippotas"], "son of Hippotes",
      "warden of the winds who bags them for Odysseus, then casts him off"),
    E("Winds", "GOD", ["Wind", "North", "South", "East", "West"], "Boreas (North), Notos (South), Euros (East), Zephyrus (West)",
      "the four winds, often personified (counts include ordinary wind/direction mentions)"),
    E("Dawn", "GOD", ["Dawn"], "rosy-fingered; the early-born; on her fair throne",
      "Eos; her rising opens each new day of the action, in fixed formulas"),
    E("Cronos", "GOD", ["Cronos"], "", "the Titan father of Zeus; nearly all hits are the patronymic 'son of Cronos' = Zeus"),
    E("Atlas", "GOD", ["Atlas"], "the deadly-minded", "the Titan who holds the pillars of sky and earth; father of Calypso"),
    E("Aeetes", "MORTAL", ["Aeetes"], "", "sorcerer-king of Aea, son of Helios and brother of Circe"),

    # ============================= MORTALS ==================================
    # -- house of Odysseus --
    E("Odysseus", "MORTAL", ["Odysseus", "Nobody"], "Nobody (Outis); of many turnings; of the many designs; sacker of cities",
      "the hero; the whole poem is his homecoming"),
    E("Penelope", "MORTAL", ["Penelope"], "watchful-minded; steady-hearted; daughter of Icarius",
      "Odysseus's wife, holding off the suitors by guile"),
    E("Telemachus", "MORTAL", ["Telemachus"], "clear-headed; godlike", "Odysseus's son, who comes of age in the Telemachy"),
    E("Laertes", "MORTAL", ["Laertes"], "", "Odysseus's aged father, withdrawn to his orchard"),
    E("Anticleia", "MORTAL", ["Anticleia"], "", "Odysseus's mother, who died of grief; met in the underworld"),
    E("Arceisius", "MORTAL", ["Arceisius"], "", "Odysseus's grandfather, father of Laertes"),
    E("Autolycus", "MORTAL", ["Autolycus"], "", "Odysseus's maternal grandfather, the master thief and oath-twister who named him"),
    E("Amphithea", "MORTAL", ["Amphithea"], "", "wife of Autolycus, Odysseus's grandmother"),
    E("Ctimene", "MORTAL", ["Ctimene"], "", "Odysseus's younger sister"),
    E("Icarius", "MORTAL", ["Icarius"], "", "Penelope's father"),
    E("Eurycleia", "MORTAL", ["Eurycleia"], "the Nurse; daughter of Ops, son of Peisenor",
      "Odysseus's old slave-nurse, who recognizes him by his scar"),
    E("Eurynome", "MORTAL", ["Eurynome"], "", "Penelope's housekeeper"),
    E("Eumaeus", "MORTAL", ["Eumaeus", "Swineherd"], "the swineherd; son of Ctesius", "the loyal swineherd, once a stolen prince of Syrie"),
    E("Philoetius", "MORTAL", ["Philoetius", "Cowherd"], "the cowherd", "the loyal cowherd who helps kill the suitors"),
    E("Dolius", "MORTAL", ["Dolius"], "", "Laertes's old gardener-slave; father of Melanthius and Melantho"),
    E("Melanthius", "MORTAL", ["Melanthius"], "", "the treacherous goatherd, mutilated at the end"),
    E("Melantho", "MORTAL", ["Melantho"], "", "the insolent slave-woman, Eurymachus's mistress"),
    E("Actoris", "MORTAL", ["Actoris"], "", "Penelope's slave, keeper of the bedchamber door"),
    E("Autonoe", "MORTAL", ["Autonoe"], "", "one of Penelope's maids"),
    E("Hippodamia", "MORTAL", ["Hippodamia"], "", "one of Penelope's maids"),
    E("Iphthime", "MORTAL", ["Iphthime"], "", "Penelope's sister; her phantom is sent to comfort her"),
    E("Phemius", "MORTAL", ["Phemius"], "son of Terpes", "the bard forced to sing for the suitors; spared"),
    E("Terpes", "MORTAL", ["Terpes"], "Terpius", "father of Phemius"),
    E("Medon", "MORTAL", ["Medon"], "", "the herald of Odysseus's house, spared with Phemius"),
    E("Mentor", "MORTAL", ["Mentor"], "", "Odysseus's steward, whose shape Athena repeatedly borrows"),
    E("Mentes", "MORTAL", ["Mentes"], "", "chieftain of the Taphians; Athena takes his form to visit Telemachus in Book 1"),
    E("Halitherses", "MORTAL", ["Halitherses"], "son of Mastor", "the old Ithacan seer who reads the eagle-omen"),
    E("Mastor", "MORTAL", ["Mastor"], "", "father of Halitherses"),
    E("Aegyptius", "MORTAL", ["Aegyptius"], "", "aged Ithacan who opens the assembly of Book 2"),
    E("Noemon", "MORTAL", ["Noemon"], "son of Phronius", "the Ithacan who lent Telemachus his ship"),
    E("Phronius", "MORTAL", ["Phronius"], "", "father of Noemon"),
    E("Peisenor", "MORTAL", ["Peisenor"], "", "an Ithacan herald; also the name of Ops's father"),
    E("Ops", "MORTAL", ["Ops"], "", "father of Eurycleia"),
    E("Ithacus", "MORTAL", ["Ithacus"], "", "eponymous founder of Ithaca; built the town fountain with Neritus and Polyctor"),
    E("Neritus", "MORTAL", ["Neritus"], "", "a founder of Ithaca (distinct from Mt Neriton)"),
    E("Mesaulius", "MORTAL", ["Mesaulius"], "", "Eumaeus's own slave, bought in his master's absence"),
    E("Icmalius", "MORTAL", ["Icmalius"], "", "craftsman who made Penelope's inlaid chair"),
    # -- the suitors --
    E("Antinous", "MORTAL", ["Antinous"], "son of Eupeithes", "the most violent suitor; first to die"),
    E("Eurymachus", "MORTAL", ["Eurymachus"], "son of Polybus", "the smooth-tongued suitor-leader; second to die"),
    E("Eupeithes", "MORTAL", ["Eupeithes"], "", "Antinous's father; leads the suitors' kin to their deaths in Book 24"),
    E("Amphinomus", "MORTAL", ["Amphinomus"], "son of Nisus", "the least brutal suitor, whom Odysseus vainly warns"),
    E("Ctesippus", "MORTAL", ["Ctesippus"], "son of Polytherses", "the suitor who throws an ox-hoof at Odysseus"),
    E("Leodes", "MORTAL", ["Leodes"], "son of Oenops", "the suitors' soothsayer; killed despite pleading"),
    E("Agelaus", "MORTAL", ["Agelaus"], "son of Damastor", "a leading suitor in the final fight"),
    E("Amphimedon", "MORTAL", ["Amphimedon"], "son of Melaneus", "the suitor whose ghost tells the tale in Book 24"),
    E("Peisander", "MORTAL", ["Peisander"], "son of Polyctor", "a suitor killed in the hall"),
    E("Eurydamas", "MORTAL", ["Eurydamas"], "", "a suitor"),
    E("Elatus", "MORTAL", ["Elatus"], "", "a suitor killed by Eumaeus"),
    E("Euryades", "MORTAL", ["Euryades"], "", "a suitor killed by Telemachus"),
    E("Demoptolemus", "MORTAL", ["Demoptolemus"], "", "a suitor"),
    E("Leocritus", "MORTAL", ["Leocritus"], "son of Evenor", "a suitor who breaks up the assembly; killed by Telemachus"),
    E("Evenor", "MORTAL", ["Evenor"], "", "father of the suitor Leocritus"),
    E("Eurynomus", "MORTAL", ["Eurynomus"], "", "a suitor, son of Aegyptius"),
    E("Antiphus", "MORTAL", ["Antiphus"], "", "an Ithacan; also a comrade eaten by the Cyclops"),
    E("Damastor", "MORTAL", ["Damastor"], "", "father of the suitor Agelaus"),
    E("Polybus", "MORTAL", ["Polybus"], "", "several men: Eurymachus's father; a Phaeacian craftsman; an Egyptian; a suitor"),
    E("Polyctor", "MORTAL", ["Polyctor"], "", "an Ithacan founder; and father of the suitor Peisander"),
    E("Polytherses", "MORTAL", ["Polytherses"], "", "father of the suitor Ctesippus"),
    E("Oenops", "MORTAL", ["Oenops"], "", "father of the suitor Leodes"),
    E("Nisus", "MORTAL", ["Nisus"], "", "lord of Dulichium, father of Amphinomus"),
    E("Irus", "MORTAL", ["Irus"], "Arnaeus", "the town beggar Odysseus thrashes; real name Arnaeus"),
    E("Arnaeus", "MORTAL", ["Arnaeus"], "", "the beggar Irus's real name"),
    E("Moulius", "MORTAL", ["Moulius"], "", "Amphinomus's herald"),
    # -- house of Atreus & the Trojan-war Greeks --
    E("Agamemnon", "MORTAL", ["Agamemnon"], "son of Atreus (Atreides); shepherd of the people",
      "leader of the host at Troy; murdered at his homecoming"),
    E("Menelaus", "MORTAL", ["Menelaus"], "fair-haired; of the great war-cry; son of Atreus (Atreides)",
      "king of Sparta, Helen's husband; hosts Telemachus"),
    E("Atreus", "MORTAL", ["Atreus", "Atreidae"], "", "father of Agamemnon and Menelaus"),
    E("Aegisthus", "MORTAL", ["Aegisthus"], "blameless; of the crooked counsels",
      "Thyestes's son; murders Agamemnon; killed by Orestes"),
    E("Thyestes", "MORTAL", ["Thyestes"], "", "Atreus's brother, father of Aegisthus"),
    E("Clytemnestra", "MORTAL", ["Clytemnestra"], "", "Agamemnon's wife and murderer"),
    E("Orestes", "MORTAL", ["Orestes"], "", "Agamemnon's son, who avenges him — the poem's model heir"),
    E("Helen", "MORTAL", ["Helen"], "", "Menelaus's wife, cause of the war, now home in Sparta"),
    E("Hermione", "MORTAL", ["Hermione"], "", "daughter of Menelaus and Helen"),
    E("Megapenthes", "MORTAL", ["Megapenthes"], "", "Menelaus's son by a slave-woman"),
    E("Achilles", "MORTAL", ["Achilles", "Aeacides"], "son of Peleus; grandson of Aeacus (Aeacides)",
      "greatest of the Achaeans; his ghost would rather be a live serf"),
    E("Peleus", "MORTAL", ["Peleus"], "", "father of Achilles"),
    E("Neoptolemus", "MORTAL", ["Neoptolemus"], "", "Achilles's son, brought from Scyros; sacker of Troy"),
    E("Patroclus", "MORTAL", ["Patroclus"], "", "Achilles's companion; shares his tomb"),
    E("Menoetius", "MORTAL", ["Menoetius"], "", "father of Patroclus"),
    E("Antilochus", "MORTAL", ["Antilochus"], "", "Nestor's son, killed at Troy; Achilles's friend"),
    E("Ajax", "MORTAL", ["Ajax"], "son of Telamon", "the greater Ajax, whose ghost will not speak to Odysseus; also Ajax son of Oileus, drowned by Poseidon"),
    E("Telamon", "MORTAL", ["Telamon"], "", "father of the greater Ajax"),
    E("Diomedes", "MORTAL", ["Diomedes"], "son of Tydeus", "Argive hero who reached home safely"),
    E("Tydeus", "MORTAL", ["Tydeus"], "", "father of Diomedes"),
    E("Idomeneus", "MORTAL", ["Idomeneus"], "", "Cretan king at Troy; figures in Odysseus's lies"),
    E("Philoctetes", "MORTAL", ["Philoctetes"], "", "the great archer who came home"),
    E("Poias", "MORTAL", ["Poias"], "", "father of Philoctetes"),
    E("Epeius", "MORTAL", ["Epeius"], "", "builder of the wooden horse"),
    E("Anticlus", "MORTAL", ["Anticlus"], "", "Achaean in the horse whom Odysseus silences"),
    E("Deiphobus", "MORTAL", ["Deiphobus"], "", "Trojan prince; Helen circles the horse with him"),
    E("Priam", "MORTAL", ["Priam"], "", "king of Troy"),
    E("Cassandra", "MORTAL", ["Cassandra"], "", "Priam's daughter, murdered beside Agamemnon"),
    E("Memnon", "MORTAL", ["Memnon"], "", "son of Dawn, killed at Troy"),
    E("Eurypylus", "MORTAL", ["Eurypylus"], "", "son of Telephus, killed by Neoptolemus"),
    E("Telephus", "MORTAL", ["Telephus"], "", "father of Eurypylus"),
    E("Nestor", "MORTAL", ["Nestor", "Gerenian"], "the Gerenian horseman", "aged king of Pylos; hosts Telemachus"),
    E("Neleus", "MORTAL", ["Neleus"], "", "father of Nestor, former king of Pylos"),
    E("Peisistratus", "MORTAL", ["Peisistratus"], "", "Nestor's youngest son, Telemachus's travelling companion"),
    E("Thrasymedes", "MORTAL", ["Thrasymedes"], "", "a son of Nestor"),
    E("Echephron", "MORTAL", ["Echephron"], "", "a son of Nestor"),
    E("Aretus", "MORTAL", ["Aretus"], "", "a son of Nestor"),
    E("Stratius", "MORTAL", ["Stratius"], "", "a son of Nestor"),
    E("Perseus", "MORTAL", ["Perseus"], "", "a son of Nestor"),
    E("Polycaste", "MORTAL", ["Polycaste"], "", "Nestor's youngest daughter, who bathes Telemachus"),
    E("Eurydice", "MORTAL", ["Eurydice"], "", "Nestor's wife"),
    E("Menelaus_house", "MORTAL", ["Eteoneus"], "", ""),  # placeholder removed below
    # attendants and lesser Greeks
    E("Eteoneus", "MORTAL", ["Eteoneus"], "son of Boethous", "Menelaus's attendant"),
    E("Boethous", "MORTAL", ["Boethous"], "", "father of Eteoneus"),
    E("Asphalion", "MORTAL", ["Asphalion"], "", "Menelaus's attendant"),
    E("Eurybates", "MORTAL", ["Eurybates"], "", "Odysseus's herald at Troy"),
    E("Alector", "MORTAL", ["Alector"], "", "Spartan whose daughter weds Megapenthes"),
    E("Eumelus", "MORTAL", ["Eumelus"], "", "husband of Penelope's sister Iphthime"),
    E("Phaedimus", "MORTAL", ["Phaedimus"], "", "king of Sidon, host of Menelaus"),
    E("Diocles", "MORTAL", ["Diocles"], "", "lord of Pherae, host of Telemachus"),
    E("Ortilochus", "MORTAL", ["Ortilochus"], "", "father of Diocles at Pherae (son of Alpheus)"),
    E("Orsilochus", "MORTAL", ["Orsilochus"], "", "son of Idomeneus, the man Odysseus claims to have killed in a lie"),
    E("Phrontis", "MORTAL", ["Phrontis"], "son of Onetor", "Menelaus's helmsman, who died at Sunium"),
    E("Onetor", "MORTAL", ["Onetor"], "", "father of Phrontis"),
    E("Phylo", "MORTAL", ["Phylo"], "", "Helen's maid"),
    E("Adreste", "MORTAL", ["Adreste"], "", "Helen's maid"),
    E("Alcippe", "MORTAL", ["Alcippe"], "", "Helen's maid"),
    E("Alcandre", "MORTAL", ["Alcandre"], "", "Egyptian woman who gave Helen gifts"),
    E("Polydamna", "MORTAL", ["Polydamna"], "", "Egyptian who gave Helen her drugs"),
    E("Thon", "MORTAL", ["Thon"], "", "Egyptian husband of Polydamna"),
    E("Rhadamanthus", "MORTAL", ["Rhadamanthus"], "", "son of Zeus, dwells in Elysium; Menelaus's promised fate"),
    E("Philomeleides", "MORTAL", ["Philomeleides"], "", "king of Lesbos whom Odysseus once out-wrestled"),
    # -- Phaeacians --
    E("Alcinous", "MORTAL", ["Alcinous"], "great-hearted; the sacred strength of Alcinous",
      "king of the Phaeacians, Odysseus's last host"),
    E("Arete", "MORTAL", ["Arete"], "", "queen of the Phaeacians; Alcinous's wife and niece"),
    E("Nausicaa", "MORTAL", ["Nausicaa"], "white-armed", "Alcinous's daughter, who finds the shipwrecked Odysseus"),
    E("Nausithous", "MORTAL", ["Nausithous"], "", "former Phaeacian king, son of Poseidon, father of Alcinous"),
    E("Rhexenor", "MORTAL", ["Rhexenor"], "", "Alcinous's brother, father of Arete"),
    E("Periboea", "MORTAL", ["Periboea"], "", "mother of Nausithous"),
    E("Eurymedon", "MORTAL", ["Eurymedon"], "", "king of the Giants, maternal ancestor of the Phaeacians"),
    E("Laodamas", "MORTAL", ["Laodamas"], "", "Alcinous's son, foremost in the games"),
    E("Halius", "MORTAL", ["Halius"], "", "a son of Alcinous, dancer"),
    E("Clytoneus", "MORTAL", ["Clytoneus"], "", "a son of Alcinous, runner"),
    E("Euryalus", "MORTAL", ["Euryalus"], "", "the Phaeacian who taunts Odysseus, then makes amends"),
    E("Echeneus", "MORTAL", ["Echeneus"], "", "the eldest Phaeacian lord, whose counsel is heeded"),
    E("Pontonous", "MORTAL", ["Pontonous"], "", "Alcinous's herald and wine-pourer"),
    E("Demodocus", "MORTAL", ["Demodocus"], "", "the blind Phaeacian bard"),
    E("Eurymedusa", "MORTAL", ["Eurymedusa"], "", "Nausicaa's aged nurse"),
    E("Dymas", "MORTAL", ["Dymas"], "", "Phaeacian sea-captain whose daughter Athena impersonates"),
    E("Phaeacian_rowers", "MORTAL",
      ["Acroneus", "Ocyalus", "Elatreus", "Nauteus", "Prymneus", "Anchialus", "Eretmeus",
       "Ponteus", "Proreus", "Thoon", "Anabesineus", "Amphialus", "Polyneus", "Tecton",
       "Naubolus", "Acastus"],
      "", "the young Phaeacians named as they line up for the games in Book 8"),
    # -- Odysseus's crew & wanderings --
    E("Eurylochus", "MORTAL", ["Eurylochus"], "", "Odysseus's second-in-command; resists Circe, then dooms the crew"),
    E("Elpenor", "MORTAL", ["Elpenor"], "", "the youngest crewman, who falls from Circe's roof and begs burial"),
    E("Perimedes", "MORTAL", ["Perimedes"], "", "a steady crewman at the underworld rite"),
    E("Polites", "MORTAL", ["Polites"], "", "the crewman dearest to Odysseus"),
    E("Antiphates", "MORTAL", ["Antiphates"], "", "the Laestrygonian king who wrecks the fleet; also a seer, son of Melampus"),
    E("Maron", "MORTAL", ["Maron"], "son of Euanthes", "priest of Apollo at Ismarus; gives the wine that fells the Cyclops"),
    E("Euanthes", "MORTAL", ["Euanthes"], "", "father of Maron"),
    E("Telemus", "MORTAL", ["Telemus"], "son of Eurymus", "the seer who foretold Polyphemus's blinding"),
    E("Eurymus", "MORTAL", ["Eurymus"], "", "father of the seer Telemus"),
    # -- Odysseus's Cretan lies & Ithaca-half strangers --
    E("Theoclymenus", "MORTAL", ["Theoclymenus"], "", "the fugitive seer Telemachus brings home; reads the suitors' doom"),
    E("Piraeus", "MORTAL", ["Piraeus"], "son of Clytius", "Telemachus's comrade, who shelters Theoclymenus"),
    E("Clytius", "MORTAL", ["Clytius"], "", "father of Piraeus"),
    E("Castor", "MORTAL", ["Castor"], "son of Hylax", "the rich Cretan Odysseus pretends to be; also the Dioscurus, Helen's brother"),
    E("Hylax", "MORTAL", ["Hylax"], "", "the Cretan grandfather in Odysseus's false tale"),
    E("Aethon", "MORTAL", ["Aethon"], "", "the false name Odysseus gives Penelope, 'Idomeneus's brother'"),
    E("Dmetor", "MORTAL", ["Dmetor"], "", "the invented king of Cyprus in a beggar's tale"),
    E("Pheidon", "MORTAL", ["Pheidon"], "", "king of the Thesprotians in Odysseus's lie"),
    E("Apheidas", "MORTAL", ["Apheidas"], "", "invented father ('Polypemon's son') in the tale told to Laertes"),
    E("Polypemon", "MORTAL", ["Polypemon"], "", "invented grandfather in the tale to Laertes"),
    E("Eperitus", "MORTAL", ["Eperitus"], "", "the false name Odysseus gives Laertes"),
    E("Arybas", "MORTAL", ["Arybas"], "", "rich Phoenician in Eumaeus's life-story"),
    E("Ctesius", "MORTAL", ["Ctesius"], "", "Eumaeus's father, king of Syrie"),
    E("Thoas", "MORTAL", ["Thoas"], "son of Andraemon", "warrior in Odysseus's night-ambush tale"),
    E("Andraemon", "MORTAL", ["Andraemon"], "", "father of Thoas"),
    # -- heroes & heroines of the underworld catalogues --
    E("Tiresias", "MORTAL", ["Tiresias", "Teiresias"], "the Theban", "the blind seer whose ghost charts Odysseus's way home"),
    E("Heracles", "MORTAL", ["Heracles"], "", "the great hero; his phantom in Hades, himself among the gods"),
    E("Amphitryon", "MORTAL", ["Amphitryon"], "", "mortal husband of Alcmene, Heracles's putative father"),
    E("Alcmene", "MORTAL", ["Alcmene"], "", "mother of Heracles by Zeus"),
    E("Megara", "MORTAL", ["Megara"], "", "Heracles's wife, daughter of Creon"),
    E("Creon", "MORTAL", ["Creon"], "", "Theban king, father of Megara"),
    E("Minos", "MORTAL", ["Minos"], "", "king of Crete, now judge of the dead"),
    E("Deucalion", "MORTAL", ["Deucalion"], "", "son of Minos, father of Idomeneus"),
    E("Ariadne", "MORTAL", ["Ariadne"], "", "Minos's daughter; slain on Dionysus's word"),
    E("Phaedra", "MORTAL", ["Phaedra"], "", "heroine seen in the underworld"),
    E("Procris", "MORTAL", ["Procris"], "", "heroine seen in the underworld"),
    E("Maera", "MORTAL", ["Maera"], "", "heroine seen in the underworld"),
    E("Clymene", "MORTAL", ["Clymene"], "", "heroine seen in the underworld"),
    E("Eriphyle", "MORTAL", ["Eriphyle"], "", "who betrayed her husband for gold"),
    E("Tyro", "MORTAL", ["Tyro"], "", "daughter of Salmoneus; bore Pelias and Neleus to Poseidon"),
    E("Salmoneus", "MORTAL", ["Salmoneus"], "", "father of Tyro"),
    E("Cretheus", "MORTAL", ["Cretheus"], "", "Tyro's husband; father of Aeson, Pheres, Amythaon"),
    E("Aeson", "MORTAL", ["Aeson"], "", "son of Tyro and Cretheus; father of Jason"),
    E("Pheres", "MORTAL", ["Pheres"], "", "son of Tyro and Cretheus"),
    E("Amythaon", "MORTAL", ["Amythaon"], "", "son of Tyro and Cretheus"),
    E("Pelias", "MORTAL", ["Pelias"], "", "son of Tyro and Poseidon, king in Iolcus"),
    E("Enipeus", "GOD", ["Enipeus"], "", "the river(-god) whose form Poseidon takes to woo Tyro"),
    E("Antiope", "MORTAL", ["Antiope"], "daughter of Asopus", "bore Amphion and Zethus to Zeus"),
    E("Amphion", "MORTAL", ["Amphion"], "", "son of Zeus and Antiope, co-founder of Thebes; also Amphion of Orchomenus"),
    E("Zethus", "MORTAL", ["Zethus"], "", "son of Zeus and Antiope, co-founder of Thebes"),
    E("Asopus", "GOD", ["Asopus"], "", "river(-god), father of Antiope"),
    E("Epicaste", "MORTAL", ["Epicaste"], "Jocasta", "Oedipus's mother and wife"),
    E("Oedipus", "MORTAL", ["Oedipus"], "", "who unknowingly wed his mother Epicaste"),
    E("Chloris", "MORTAL", ["Chloris"], "", "Neleus's wife, mother of Nestor and Pero"),
    E("Pero", "MORTAL", ["Pero"], "", "Neleus's daughter, won by the cattle-feat"),
    E("Periclymenus", "MORTAL", ["Periclymenus"], "", "a son of Neleus"),
    E("Chromius", "MORTAL", ["Chromius"], "", "a son of Neleus"),
    E("Iphicles", "MORTAL", ["Iphicles"], "", "owner of the cattle in the Melampus story"),
    E("Melampus", "MORTAL", ["Melampus"], "", "the seer-ancestor who won Pero's hand for his brother"),
    E("Leda", "MORTAL", ["Leda"], "", "mother of Castor and Polydeuces"),
    E("Polydeuces", "MORTAL", ["Polydeuces"], "", "the immortal twin, brother of Castor"),
    E("Tyndareus", "MORTAL", ["Tyndareus"], "", "mortal husband of Leda"),
    E("Iphimedeia", "MORTAL", ["Iphimedeia"], "", "mother of the giant Aloadae by Poseidon"),
    E("Aloeus", "MORTAL", ["Aloeus"], "", "putative father of the Aloadae"),
    E("Otus", "MORTAL", ["Otus"], "", "giant son of Iphimedeia, who piled the mountains"),
    E("Ephialtes", "MORTAL", ["Ephialtes"], "", "giant brother of Otus"),
    E("Theseus", "MORTAL", ["Theseus"], "", "Athenian hero named among the great dead"),
    E("Peirithous", "MORTAL", ["Peirithous", "Pirithous"], "", "Lapith king, Theseus's companion"),
    E("Sisyphus", "MORTAL", ["Sisyphus"], "", "punished in Hades, rolling his stone"),
    E("Tantalus", "MORTAL", ["Tantalus"], "", "punished in Hades by the receding water and fruit"),
    E("Tityus", "MORTAL", ["Tityus"], "", "giant punished in Hades for assaulting Leto"),
    E("Orion", "MORTAL", ["Orion"], "", "the hunter, seen driving game in Hades; and the constellation"),
    E("Iasion", "MORTAL", ["Iasion"], "", "mortal loved by Demeter, killed by Zeus"),
    E("Tithonus", "MORTAL", ["Tithonus"], "", "mortal husband of Dawn"),
    E("Cadmus", "MORTAL", ["Cadmus"], "", "founder of Thebes, father of Ino"),
    E("Erechtheus", "MORTAL", ["Erechtheus"], "", "earthborn king of Athens"),
    E("Iphitus", "MORTAL", ["Iphitus"], "", "son of Eurytus; gave Odysseus the great bow"),
    E("Eurytus", "MORTAL", ["Eurytus"], "", "archer who challenged the gods; owner of the bow"),
    E("Pandareus", "MORTAL", ["Pandareus"], "", "father of the nightingale Aedon and of the storm-snatched girls"),
    E("Amphiaraus", "MORTAL", ["Amphiaraus"], "", "the seer-warrior swallowed by the earth at Thebes"),
    E("Alcmaeon", "MORTAL", ["Alcmaeon"], "", "son of Amphiaraus"),
    E("Amphilochus", "MORTAL", ["Amphilochus"], "", "son of Amphiaraus"),
    E("Oicles", "MORTAL", ["Oicles"], "", "father of Amphiaraus"),
    E("Mantius", "MORTAL", ["Mantius"], "", "son of Melampus, in the seers' pedigree"),
    E("Cleitus", "MORTAL", ["Cleitus"], "", "grandson of Melampus, carried off by Dawn"),
    E("Polypheides", "MORTAL", ["Polypheides"], "", "seer son of Mantius, father of Theoclymenus"),
    E("Phylacus", "MORTAL", ["Phylacus"], "", "owner of the cattle in the Melampus tale; lord of Phylace"),
    E("Ormenus", "MORTAL", ["Ormenus"], "", "father of Ctesius in Eumaeus's story"),
    E("Iasus", "MORTAL", ["Iasus"], "", "father of Amphion of Orchomenus; also of Dmetor of Cyprus"),
    E("Itylus", "MORTAL", ["Itylus"], "", "the boy killed by his mother Aedon, the nightingale of the lament"),
    E("Melaneus", "MORTAL", ["Melaneus"], "", "father of the suitor Amphimedon"),
    E("Laerces", "MORTAL", ["Laerces"], "", "the goldsmith who gilds Nestor's ox-horns"),
    E("Clymenus", "MORTAL", ["Clymenus"], "", "father of Nestor's wife Eurydice"),
    E("Ilus", "MORTAL", ["Ilus"], "son of Mermerus", "lord of Ephyra who refused Odysseus poison"),
    E("Mermerus", "MORTAL", ["Mermerus"], "", "father of Ilus of Ephyra"),
    E("Echetus", "MORTAL", ["Echetus"], "", "the proverbial mainland ogre-king, 'maimer of all men'"),
    E("Jason", "MORTAL", ["Jason"], "", "leader of the Argonauts, past the Clashing Rocks"),
    E("Alcimus", "MORTAL", ["Alcimus"], "", "father of Mentor"),

    # ============================= PEOPLES ==================================
    E("Achaeans", "PEOPLE", ["Achaeans", "Achaean"], "the Argives; the Danaans", "the Greeks — the poem's default name for the host"),
    E("Argives", "PEOPLE", ["Argives", "Argive"], "", "the Greeks (from Argos), interchangeable with Achaeans"),
    E("Danaans", "PEOPLE", ["Danaans", "Danaan"], "", "the Greeks — the third synonym for the host"),
    E("Trojans", "PEOPLE", ["Trojans", "Trojan"], "", "the people of Troy"),
    E("Phaeacians", "PEOPLE", ["Phaeacians", "Phaeacian"], "of the long oars, men famed for ships", "the seafaring people of Scheria"),
    E("Cicones", "PEOPLE", ["Cicones"], "", "Thracian allies of Troy; Odysseus's first landfall and first loss"),
    E("Lotus-eaters", "PEOPLE", ["Lotus"], "", "the people whose flower erases the wish to return home"),
    E("Laestrygonians", "PEOPLE", ["Laestrygonians", "Laestrygonian"], "", "the cannibal giants who destroy eleven ships"),
    E("Cephallenians", "PEOPLE", ["Cephallenians", "Cephallenian"], "", "Odysseus's own subjects across his island realm"),
    E("Taphians", "PEOPLE", ["Taphians", "Taphian"], "", "seafarers and slave-raiders; Mentes's people"),
    E("Pylians", "PEOPLE", ["Pylians"], "", "Nestor's people"),
    E("Cretans", "PEOPLE", ["Cretans", "Cretan"], "", "the people of Crete, prominent in Odysseus's lies"),
    E("Egyptians", "PEOPLE", ["Egyptians", "Egyptian"], "", "the people of Egypt"),
    E("Phoenicians", "PEOPLE", ["Phoenicians", "Phoenician"], "", "the traders and slavers of Sidon"),
    E("Sidonians", "PEOPLE", ["Sidonians"], "", "the people of Sidon in Phoenicia"),
    E("Thesprotians", "PEOPLE", ["Thesprotians", "Thesprotian"], "", "the mainland people (and land) of Odysseus's Thesprotian cover-story"),
    E("Ethiopians", "PEOPLE", ["Ethiopians"], "", "the remotest of men, split east and west; Poseidon's hosts"),
    E("Epeians", "PEOPLE", ["Epeians"], "", "the people of Elis"),
    E("Cauconians", "PEOPLE", ["Cauconians"], "", "a people of the western Peloponnese"),
    E("Myrmidons", "PEOPLE", ["Myrmidons", "Myrmidon"], "", "Achilles's Thessalian people"),
    E("Cadmeians", "PEOPLE", ["Cadmeians"], "", "the Thebans, people of Cadmus"),
    E("Dorians", "PEOPLE", ["Dorians"], "", "one of the peoples of Crete"),
    E("Pelasgians", "PEOPLE", ["Pelasgians"], "", "an old people of Crete"),
    E("Cydonians", "PEOPLE", ["Cydonians"], "", "a people of western Crete"),
    E("Sicilians", "PEOPLE", ["Sicilians", "Sicilian"], "", "the people of Sicania; a slave-woman of Laertes"),
    E("Giants", "PEOPLE", ["Giants"], "", "the lawless mythic race, kin to the early Phaeacian line"),
    E("Cimmerians", "PEOPLE", ["Cimmerian"], "", "the sunless people at the edge of Ocean, by the entrance to Hades"),
    E("Solymi", "PEOPLE", ["Solymi"], "", "an eastern people; their hills are where Poseidon spots Odysseus"),
    E("Sintians", "PEOPLE", ["Sintians"], "", "the wild people of Lemnos who received the fallen Hephaestus"),
    E("Erembi", "PEOPLE", ["Erembi"], "", "a far people Menelaus visited"),
    E("Aetolians", "PEOPLE", ["Aetolian"], "", "the people of the mainland liar who cheated Eumaeus"),
    E("Lapiths", "PEOPLE", ["Lapiths"], "", "the people who fought the Centaurs at Peirithous's wedding"),
    E("Centaurs", "OTHER", ["Centaurs", "Centaur", "Eurytion"], "the Centaur = Eurytion", "the half-horse creatures routed by the Lapiths"),

    # ============================== PLACES ==================================
    E("Ithaca", "PLACE", ["Ithaca", "Ithacan"], "sea-circled; rocky Ithaca", "Odysseus's island kingdom, the goal of the poem"),
    E("Pylos", "PLACE", ["Pylos"], "", "Nestor's kingdom on the western Peloponnese"),
    E("Sparta", "PLACE", ["Sparta"], "", "Menelaus's city; Telemachus's second stop"),
    E("Lacedaemon", "PLACE", ["Lacedaemon"], "", "the land of Sparta"),
    E("Scheria", "PLACE", ["Scheria"], "the land of the Phaeacians", "the Phaeacians' island, Odysseus's last stop before home"),
    E("Ogygia", "PLACE", ["Ogygia"], "", "Calypso's island, the navel of the sea"),
    E("Aeaea", "PLACE", ["Aeaea"], "", "Circe's island"),
    E("Thrinacia", "PLACE", ["Thrinacia"], "", "the island of Helios's cattle"),
    E("Troy", "PLACE", ["Troy", "Ilium"], "Ilium", "the sacked city; the war's setting"),
    E("Crete", "PLACE", ["Crete"], "", "the great southern island; the backdrop of Odysseus's lies"),
    E("Egypt", "PLACE", ["Egypt"], "", "the land — and the river (the Nile) — of Menelaus's detour"),
    E("Dulichium", "PLACE", ["Dulichium"], "", "island near Ithaca, home of many suitors"),
    E("Same", "PLACE", ["Samos", "Same"], "Samos", "island of Odysseus's realm (Cephallenia); a suitor stronghold"),
    E("Zacynthus", "PLACE", ["Zacynthus"], "", "wooded island of Odysseus's realm"),
    E("Argos", "PLACE", ["Argos"], "", "the Peloponnesian city/region (not Argus the hound)"),
    E("Mycenae", "PLACE", ["Mycenae"], "", "Agamemnon's city"),
    E("Mycene", "MORTAL", ["Mycene"], "of the lovely crown", "heroine and eponym of Mycenae, named in the catalogue of women (2.120)"),
    E("Athens", "PLACE", ["Athens"], "", "city of Erechtheus and Athena"),
    E("Thebes", "PLACE", ["Thebes", "Theban"], "", "Boeotian Thebes of the seven gates; and Egyptian Thebes of the hundred"),
    E("Orchomenus", "PLACE", ["Orchomenus"], "", "the Minyan city of fabled wealth"),
    E("Hellas", "PLACE", ["Hellas"], "", "northern Greece; with 'mid-Argos', a name for the whole land"),
    E("Achaea", "PLACE", ["Achaea"], "", "Greece, the Achaeans' land"),
    E("Elis", "PLACE", ["Elis"], "", "region of the Epeians in the western Peloponnese"),
    E("Pherae", "PLACE", ["Pherae"], "", "waypoint between Pylos and Sparta; also Eumelus's Thessalian town"),
    E("Messene", "PLACE", ["Messene"], "", "region where young Odysseus met Iphitus"),
    E("Ephyra", "PLACE", ["Ephyra"], "", "town Odysseus sought arrow-poison from"),
    E("Olympus", "PLACE", ["Olympus"], "", "the gods' seat, above weather and change"),
    E("Ocean", "PLACE", ["Ocean"], "", "the world-encircling river; beyond it lie the dead"),
    E("Erebus", "PLACE", ["Erebus"], "", "the nether darkness; the dead are summoned up from it"),
    E("Elysium", "PLACE", ["Elysian"], "the Elysian plain", "the deathless plain promised to Menelaus"),
    E("Acheron", "PLACE", ["Acheron"], "", "underworld river at the meeting of the waters"),
    E("Cocytus", "PLACE", ["Cocytus"], "", "underworld river, branch of Styx"),
    E("Pyriphlegethon", "PLACE", ["Pyriphlegethon"], "", "the underworld river of fire"),
    E("Styx", "PLACE", ["Styx"], "", "the river of the gods' unbreakable oath"),
    E("Aegae", "PLACE", ["Aegae"], "", "Poseidon's undersea seat"),
    E("Lemnos", "PLACE", ["Lemnos"], "", "Hephaestus's island"),
    E("Lesbos", "PLACE", ["Lesbos"], "", "island where Odysseus wrestled Philomeleides"),
    E("Chios", "PLACE", ["Chios"], "", "island on Nestor's route home"),
    E("Psyria", "PLACE", ["Psyria"], "", "islet passed on the voyage from Troy"),
    E("Tenedos", "PLACE", ["Tenedos"], "", "island off Troy, first anchorage of the homeward Greeks"),
    E("Euboea", "PLACE", ["Euboea"], "", "the long island; the Phaeacians' farthest sail"),
    E("Delos", "PLACE", ["Delos"], "", "Apollo's island; site of the palm Odysseus recalls to Nausicaa"),
    E("Ortygia", "PLACE", ["Ortygia"], "", "the island where Artemis slew Orion"),
    E("Syrie", "PLACE", ["Syrie"], "", "Eumaeus's home island, above Ortygia"),
    E("Cyprus", "PLACE", ["Cyprus"], "", "island of Aphrodite's Paphian shrine"),
    E("Paphos", "PLACE", ["Paphos"], "", "Aphrodite's precinct on Cyprus"),
    E("Cythera", "PLACE", ["Cythera"], "", "island off Malea, blown past on the way to the Lotus-eaters"),
    E("Phoenicia", "PLACE", ["Phoenicia"], "", "the Levantine trading coast"),
    E("Sidon", "PLACE", ["Sidon"], "", "the Phoenician city"),
    E("Libya", "PLACE", ["Libya"], "", "the North African land of endless lambs"),
    E("Thrace", "PLACE", ["Thrace"], "", "northern land; the Ciconian coast"),
    E("Sicania", "PLACE", ["Sicania"], "", "Sicily, edge of the known world in the poem's geography"),
    E("Dodona", "PLACE", ["Dodona"], "", "the oak-oracle of Zeus Odysseus claims to have consulted"),
    E("Pytho", "PLACE", ["Pytho"], "", "Delphi, seat of Apollo's oracle"),
    E("Parnassus", "PLACE", ["Parnassus"], "", "the mountain where the boar gashed young Odysseus, leaving the scar"),
    E("Malea", "PLACE", ["Malea"], "", "the cape whose storms scatter homeward ships"),
    E("Sunium", "PLACE", ["Sunium"], "", "the Attic headland where Menelaus's helmsman died"),
    E("Geraestus", "PLACE", ["Geraestus"], "", "the Euboean cape of safe landfall"),
    E("Gyrae", "PLACE", ["Gyrae"], "", "the rocks where Poseidon drowned the lesser Ajax"),
    E("Aegyptus_river", "PLACE", ["Egyptian"], "", "(adjective form; see Egypt)"),
    E("Pharos", "PLACE", ["Pharos"], "", "the island off Egypt where Menelaus was becalmed"),
    E("Cnossus", "PLACE", ["Cnossus"], "", "Minos's Cretan capital"),
    E("Gortyn", "PLACE", ["Gortyn"], "", "Cretan city near the wreck of Menelaus's ships"),
    E("Phaestus", "PLACE", ["Phaestus"], "", "Cretan town by the same reef"),
    E("Amnisus", "PLACE", ["Amnisus"], "", "the Cretan harbor with Eileithyia's cave"),
    E("Iolcus", "PLACE", ["Iolcus"], "", "Pelias's city, whence the Argo sailed"),
    E("Phthia", "PLACE", ["Phthia"], "", "Achilles's Thessalian homeland"),
    E("Phylace", "PLACE", ["Phylace"], "", "town of Phylacus in the Melampus tale"),
    E("Oechalia", "PLACE", ["Oechalia"], "", "city of Eurytus the archer"),
    E("Scyros", "PLACE", ["Scyros"], "", "island where Neoptolemus was raised"),
    E("Marathon", "PLACE", ["Marathon"], "", "Attic town, with Athens in Athena's flight"),
    E("Hyperesia", "PLACE", ["Hyperesia"], "", "town in the seers' pedigree"),
    E("Chalcis", "PLACE", ["Chalcis"], "", "stream in Elis passed on Telemachus's night-sail"),
    E("Crouni", "PLACE", ["Crouni"], "", "spring-place in Elis on the same run"),
    E("Pheae", "PLACE", ["Pheae"], "", "coastal town passed on the night-sail"),
    E("Ismarus", "PLACE", ["Ismarus"], "", "the Ciconian city Odysseus sacks"),
    E("Telepylus", "PLACE", ["Telepylus"], "", "the Laestrygonian stronghold, city of Lamus"),
    E("Lamus", "PLACE", ["Lamus"], "", "founder-eponym of the Laestrygonian city"),
    E("Artacia", "PLACE", ["Artacia"], "", "the spring in the Laestrygonian land"),
    E("Apeire", "PLACE", ["Apeire"], "", "the land Nausicaa's nurse Eurymedusa was carried from"),
    E("Asteris", "PLACE", ["Asteris"], "", "the islet where the suitors lie in ambush for Telemachus"),
    E("Dia", "PLACE", ["Dia"], "", "the island (Naxos) where Artemis slew Ariadne"),
    E("Taphos", "PLACE", ["Taphos"], "", "Mentes's island, home of the Taphian seafarers"),
    E("Panopeus", "PLACE", ["Panopeus"], "", "Phocian town near which Tityus lay stretched in Hades"),
    E("Hypereia", "PLACE", ["Hypereia"], "", "the Phaeacians' former home, near the Cyclopes"),
    E("Pieria", "PLACE", ["Pieria"], "", "the mountain over which Hermes swoops to Ogygia"),
    E("Neriton", "PLACE", ["Neriton"], "", "the tall wooded mountain of Ithaca"),
    E("Neion", "PLACE", ["Neion"], "", "another Ithacan height, above the harbor"),
    E("Nericus", "PLACE", ["Nericus"], "", "a mainland town Laertes once took"),
    E("Rheithron", "PLACE", ["Rheithron"], "", "the Ithacan harbor where Mentes's ship lies"),
    E("Arethusa", "PLACE", ["Arethusa"], "", "the spring by Raven's Rock where Eumaeus's pigs drink"),
    E("Erymanthus", "PLACE", ["Erymanthus"], "", "the mountain of Artemis's boar-hunt simile"),
    E("Taygetus", "PLACE", ["Taygetus"], "", "the mountain of the same simile"),
    E("Cyllene", "PLACE", ["Cyllene"], "", "Hermes's mountain, whence he leads the suitors' souls"),
    E("Pelion", "PLACE", ["Pelion"], "", "mountain the giants piled to storm heaven"),
    E("Ossa", "PLACE", ["Ossa"], "", "mountain piled with Pelion in the giants' assault"),
    E("Iardanus", "PLACE", ["Iardanus"], "", "Cretan river of the Cydonians"),
    E("Alpheus", "PLACE", ["Alpheus"], "", "the great river of Elis (a god); ancestor of Ortilochus"),
    E("Aegae_river", "PLACE", ["Aegae"], "", "(see above)"),
    E("Alybas", "PLACE", ["Alybas"], "", "the far town Odysseus invents as his home for Laertes"),
    E("Temese", "PLACE", ["Temese"], "", "the copper-port Mentes claims to be sailing to"),
    E("Hellespont", "PLACE", ["Hellespont"], "", "the strait by the Achaean tombs"),
    E("Mimas", "PLACE", ["Mimas"], "", "the headland opposite Chios on Nestor's route"),
    E("Planctae", "PLACE", ["Rocks"], "the Wandering Rocks; the Clashing Rocks", "the crashing rocks only the Argo passed (counts include ordinary 'rocks')"),

    # ======================== OTHER (animals, things) =======================
    E("Argus", "OTHER", ["Argus"], "", "Odysseus's old hound, who knows him and dies (Book 17). NB: 'slayer of Argus' = Hermes, a different Argus (the giant)"),
    E("Argo", "OTHER", ["Argo"], "", "the ship 'known to all', the only one to pass the Wandering Rocks"),
    E("Moly", "OTHER", ["Moly"], "", "the god-given herb that proofs Odysseus against Circe's drug"),
    E("Lampus", "OTHER", ["Lampus"], "", "one of the two colts that draw the chariot of Dawn"),
    E("Phaethon", "OTHER", ["Phaethon"], "", "the other colt of Dawn's chariot"),
    E("Hound-of-Hades", "OTHER", ["Hound"], "Cerberus", "the hound Heracles was sent to fetch from the underworld"),
    E("Constellations", "OTHER", ["Boötes", "Pleiades", "Bear", "Wagon"],
      "the Wain / the Bear; Boötes; the Pleiades", "the stars Odysseus steers by leaving Ogygia (with Orion)"),
]


def load_occ():
    return json.load(open(OCC, encoding="utf-8"))


def fmt_books(books):
    if not books:
        return ""
    parts, start, prev = [], books[0], books[0]
    for b in books[1:]:
        if b == prev + 1:
            prev = b
            continue
        parts.append(f"{start}-{prev}" if start != prev else f"{start}")
        start = prev = b
    parts.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ", ".join(parts)


def build():
    occ = load_occ()
    used = set()
    dup = defaultdict(list)
    missing = []
    rows = []

    # drop placeholder rows whose only purpose was scaffolding
    entries = [e for e in REGISTRY if not e["headword"].endswith("_placeholder")
               and e["headword"] not in ("Menelaus_house", "Aegae_river", "Aegyptus_river")]

    def refkey(ref):
        b, l = ref.split(".")
        return (int(b), int(l))

    for e in entries:
        count = 0
        books = set()
        refs = set()
        real_tokens = []
        for t in e["tokens"]:
            if t in occ:
                count += occ[t]["count"]
                books |= set(occ[t]["books"])
                refs |= set(occ[t]["refs"])
                real_tokens.append(t)
                dup[t].append(e["headword"])
                used.add(t)
            else:
                missing.append((e["headword"], t))
        e["_count"] = count
        e["_books"] = sorted(books)
        e["_refs"] = sorted(refs, key=refkey)
        rows.append(e)

    unclassified = sorted(t for t in occ if t not in used)
    collisions = {t: hs for t, hs in dup.items() if len(hs) > 1}
    return rows, unclassified, collisions, missing


def write_md(rows):
    order = ["MORTAL", "GOD", "PEOPLE", "PLACE", "OTHER"]
    titles = {
        "MORTAL": "Mortals", "GOD": "Gods & divine beings",
        "PEOPLE": "Peoples & groups", "PLACE": "Places", "OTHER": "Animals, objects & the sky",
    }
    by_cat = defaultdict(list)
    for r in rows:
        by_cat[r["cat"]].append(r)

    out = ["# Name index — master registry (Phase 2, full coverage)\n"]
    out.append(
        "Every real proper name in the poem, classified and canonicalized. Generated "
        "by `tools/build_registry.py` from a curated classification joined against "
        "`index/occurrences.json`; hit-counts and book coverage are computed, so this "
        "stays true to the text if a line is ever revised. Aliases and same-name "
        "collisions are resolved here and in `canon.md`. This is the work list Phase 3 "
        "draws from — one entry per headword.\n"
    )
    total = sum(1 for _ in rows)
    out.append(f"**{total} headwords.** Categories: "
               + ", ".join(f"{titles[c]} ({len(by_cat[c])})" for c in order) + ".\n")

    for c in order:
        items = sorted(by_cat[c], key=lambda r: (-r["_count"], r["headword"]))
        out.append(f"\n## {titles[c]}\n")
        out.append("| Headword | Hits | Books | Aliases / epithets | Note |")
        out.append("| --- | ---: | --- | --- | --- |")
        for r in items:
            hw = r["headword"]
            out.append(f"| **{hw}** | {r['_count']} | {fmt_books(r['_books'])} "
                       f"| {r['aliases']} | {r['note']} |")
    return "\n".join(out) + "\n"


def write_registry_json(rows):
    """Machine-readable registry with citations joined in — the source the Phase 3
    slicer turns into per-writer work packets."""
    data = [
        {
            "headword": r["headword"],
            "cat": r["cat"],
            "aliases": r["aliases"],
            "note": r["note"],
            "count": r["_count"],
            "books": r["_books"],
            "refs": r["_refs"],
        }
        for r in sorted(rows, key=lambda r: r["headword"].lower())
    ]
    (ROOT / "index" / "registry.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main():
    rows, unclassified, collisions, missing = build()
    OUT.write_text(write_md(rows), encoding="utf-8")
    write_registry_json(rows)

    print(f"wrote {OUT} and index/registry.json — {len(rows)} headwords")
    if missing:
        print(f"\n[!] {len(missing)} tokens in REGISTRY not found in occurrences.json:")
        for hw, t in missing:
            print(f"    {hw}: {t!r}")
    if collisions:
        print(f"\n[!] {len(collisions)} tokens claimed by >1 headword:")
        for t, hs in collisions.items():
            print(f"    {t!r}: {hs}")
    print(f"\n{len(unclassified)} unclassified tokens (noise + any misses):")
    print("  " + "  ".join(unclassified))
    return 0


if __name__ == "__main__":
    sys.exit(main())
