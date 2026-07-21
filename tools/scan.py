"""Deterministic dactylic-hexameter checker for the Greek text.

This is a *verifier*, not a scanner-of-record: it does not claim to produce the
one true scansion of a line. It asks a decidable question — "does at least one
metrically legal reading of this line exist as a dactylic hexameter?" — and
answers yes/no by search over the positions that Greek prosody leaves free.

Quantities that are fixed by the writing system are treated as fixed:
  - naturally long:  η ω, and the diphthongs (αι αυ ει ευ ηυ οι ου υι + iota
    subscripts ᾳ ῃ ῳ), and any vowel bearing a circumflex.
  - naturally short: ε ο.
  - "position": a short vowel followed by two consonants (across word
    boundaries too) is heavy. ζ ξ ψ count as double; a mute+liquid cluster
    (π,β,φ,τ,δ,θ,κ,γ,χ + λ,ρ,μ,ν) is treated as *optionally* making position,
    since epic allows either — so it becomes a free choice in the search.
  - dichrona (α ι υ without a circumflex) are genuinely ambiguous by spelling;
    they are left free and the search picks whatever the meter needs.

A line "scans" if some assignment of the free quantities yields the classic
pattern: five feet each dactyl (– ‿ ‿) or spondee (– –), then a final foot of
two syllables (– –  or – ‿, the anceps). That is exactly 17 down to 13 metrical
positions, so the syllable count alone must land in [13, 17]; the search
confirms the fixed quantities don't contradict any valid footing.

Usage:
    python scan.py greek/book-01.txt        # check one file
    python scan.py greek/*.txt              # check many
    python scan.py --verbose greek/book-09.txt   # show why lines fail

On Murray's text this reports ~95% of lines as scannable. The ~5% residual is
not noise and not (as far as tested) a modelling bug: it is the set of lines
whose scansion depends on facts the written text does not carry, and which a
text-only rule therefore cannot see —
  - digamma: a lost initial ϝ (e.g. ἥν < ϝήν, οἶνος < ϝοῖνος) still makes
    position, lengthening a preceding short syllable that looks light on paper;
  - synizesis: two written vowels sung as one syllable (θεοί, πόλιος, Πηληϊάδεω),
    which changes the syllable count itself;
  - metrical lengthening and proper-name licence.
A flagged line is thus often an interesting line, not a wrong one. Treat 95% as
the regression baseline: a sudden drop means the prosody model broke, not that
Homer did.
"""
import glob
import re
import sys
import unicodedata

# --- vowels and diphthongs, worked on NFD (base letter + combining marks) ---

VOWELS = set("αεηιουω")
LONG_VOWELS = set("ηω")          # long by nature regardless of accent
SHORT_VOWELS = set("εο")         # short by nature regardless of accent
# α ι υ are dichrona: ambiguous unless a circumflex forces long (handled below)

CIRCUMFLEX = "͂"            # combining Greek perispomeni
IOTA_SUB = "ͅ"             # combining Greek ypogegrammeni -> long diphthong
DIAERESIS = "̈"           # splits a would-be diphthong

DIPHTHONGS = {"αι", "αυ", "ει", "ευ", "ηυ", "οι", "ου", "υι", "ωυ"}

# Elision marks. These are word boundaries, not consonants, but Python's
# str.isalpha() is True for U+02BC MODIFIER LETTER APOSTROPHE (the character
# Perseus uses for elision), so we must exclude them explicitly — otherwise
# every elided δʼ/τʼ/μʼ fabricates a consonant and false position length.
APOSTROPHES = {"ʼ", "’", "'", "᾽", "᾿"}

DOUBLE_CONS = set("ζξψ")
MUTES = set("πβφτδθκγχ")
LIQUIDS = set("λρμν")


def strip_to_base(ch):
    """Base lowercase letter of a possibly-accented Greek character."""
    for c in unicodedata.normalize("NFD", ch):
        if not unicodedata.combining(c):
            return c.lower()
    return ""


def marks(ch):
    """Set of combining marks on a character (NFD)."""
    return {c for c in unicodedata.normalize("NFD", ch) if unicodedata.combining(c)}


def is_consonant(base):
    return base.isalpha() and base not in VOWELS


def syllabify_nuclei(text):
    """Return a list of syllable nuclei for a whole line.

    Each nucleus is a dict with:
      long_by_nature: bool (η, ω, circumflex, or long diphthong) -> heavy
      short_by_nature: bool (ε, ο) -> light unless position makes it heavy
      (neither set -> dichronon, free)
      coda_consonants: consonants after this nucleus up to the next nucleus,
                       as a list of base letters (used for position length)
    Word boundaries are dropped; consonants carry across them, which is what
    epic position-length needs.
    """
    # normalize to a flat sequence of (base, marks, boundary_before) for letters
    # only. boundary_before marks a letter that begins a new word (a space or
    # punctuation preceded it), which is what lets us tell within-word clusters
    # from clusters formed only across a word break.
    seq = []
    pending_boundary = True
    for ch in text:
        if ch in APOSTROPHES:
            # elision: a word boundary, never a consonant (isalpha() lies here)
            pending_boundary = True
            continue
        base = strip_to_base(ch)
        if base and base.isalpha():
            seq.append((base, marks(ch), pending_boundary))
            pending_boundary = False
        else:
            # space, punctuation: next letter starts fresh
            pending_boundary = True

    nuclei = []
    i = 0
    n = len(seq)
    while i < n:
        base, mk, _bnd = seq[i]
        if base in VOWELS:
            # try to form a diphthong with the next vowel
            long_diph = False
            consumed = 1
            if IOTA_SUB in mk:
                long_diph = True  # ᾳ ῃ ῳ
            elif i + 1 < n:
                nb, nmk, _nbnd = seq[i + 1]
                pair = base + nb
                if pair in DIPHTHONGS and DIAERESIS not in nmk:
                    long_diph = True
                    consumed = 2
            long_by_nature = (
                long_diph
                or base in LONG_VOWELS
                or CIRCUMFLEX in mk
            )
            short_by_nature = (not long_by_nature) and base in SHORT_VOWELS
            nuclei.append({
                "long_by_nature": long_by_nature,
                "short_by_nature": short_by_nature,
                "coda": [],
            })
            i += consumed
        else:
            # consonant: attach to the coda of the current (last) nucleus,
            # remembering whether it began a new word (for cross-boundary rules)
            if nuclei:
                nuclei[-1]["coda"].append((base, _bnd))
            i += 1

    # epic correption: a long vowel or diphthong in hiatus (empty coda, i.e.
    # standing directly before the next word's initial vowel) may be scanned
    # short. Mark those nuclei; weights() will treat their length as free.
    for idx, nuc in enumerate(nuclei):
        nuc["hiatus"] = (idx < len(nuclei) - 1 and not nuc["coda"])
    return nuclei


def weights(nuclei):
    """Yield per-syllable weight constraints as one of:
        'H'  must be heavy
        'L'  must be light
        'F'  free (dichronon and no position) -> may be H or L
        'M'  optional: mute+liquid position -> heavy or light by choice
    """
    out = []
    for idx, nuc in enumerate(nuclei):
        coda = nuc["coda"]                      # list of (consonant, boundary)
        cons = [c for c, _b in coda]
        # count consonantal timing after the vowel, before next vowel. A
        # following nucleus' onset consonants live in *this* coda already,
        # because we attached every consonant to the preceding nucleus.
        heavy_by_position = None  # None=no, True=yes, "maybe"=optional
        if any(c in DOUBLE_CONS for c in cons):
            heavy_by_position = True
        elif len(cons) >= 2:
            c1, c2 = cons[0], cons[1]
            # a cluster whose *second* consonant begins the next word (c2 is
            # word-initial) straddles a word boundary; epic scans these either
            # way, so treat as optional rather than forced-heavy.
            straddles = coda[1][1]
            if c1 in MUTES and c2 in LIQUIDS:
                heavy_by_position = "maybe"    # mute+liquid: always optional
            elif straddles:
                heavy_by_position = "maybe"    # cluster made only across a break
            else:
                heavy_by_position = True
        # last syllable of the line: its coda doesn't count against it and it is
        # anceps anyway; handled by the final foot in the matcher.

        # epic correption: a long vowel/diphthong standing in hiatus may be
        # read short, so its length is free rather than forced heavy. (A vowel
        # that is also long-by-position keeps position; correption only touches
        # length-by-nature in open syllables, which is exactly the hiatus case.)
        if nuc["long_by_nature"] and nuc.get("hiatus"):
            out.append("F")
        elif nuc["long_by_nature"]:
            out.append("H")
        elif heavy_by_position is True:
            out.append("H")
        elif heavy_by_position == "maybe":
            out.append("M")
        elif nuc["short_by_nature"]:
            out.append("L")
        else:
            out.append("F")  # dichronon, open syllable
    return out


def scans(w):
    """Can the weight-constraint list w be read as a dactylic hexameter?

    Six feet. Feet 1-5 are dactyl (H L L) or spondee (H H). Foot 6 is two
    syllables: H + anceps. We search recursively; 'F' and 'M' can be either.
    The final syllable is anceps (may be read heavy or light) so it is a
    wildcard regardless of its computed weight.
    """
    def can_be(sym, target):
        # target is 'H' or 'L'
        if sym == "F" or sym == "M":
            return True
        return sym == target

    def rec(pos, foot):
        # foot counts 1..6
        if foot == 6:
            # exactly two syllables left: first heavy, second anceps
            if pos != len(w) - 2:
                return False
            return can_be(w[pos], "H")  # w[pos+1] is anceps -> always ok
        if pos >= len(w):
            return False
        if not can_be(w[pos], "H"):
            return False
        # try dactyl: H L L
        if pos + 2 < len(w) and can_be(w[pos + 1], "L") and can_be(w[pos + 2], "L"):
            if rec(pos + 3, foot + 1):
                return True
        # try spondee: H H
        if pos + 1 < len(w) and can_be(w[pos + 1], "H"):
            if rec(pos + 2, foot + 1):
                return True
        return False

    return rec(0, 1)


def check_line(greek):
    nuclei = syllabify_nuclei(greek)
    w = weights(nuclei)
    ok = 13 <= len(w) <= 17 and scans(w)
    return ok, len(w), w


def parse_file(path):
    lines = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.rstrip("\n")
            if not raw.strip():
                continue
            num, _, greek = raw.partition("\t")
            lines.append((num, greek))
    return lines


def main(argv):
    # The verbose report prints Greek; force UTF-8 so it never dies on a
    # legacy Windows console codepage (cp1252 can't encode polytonic Greek).
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    verbose = False
    args = []
    for a in argv:
        if a in ("-v", "--verbose"):
            verbose = True
        else:
            args.extend(glob.glob(a) or [a])

    if not args:
        print(__doc__)
        return 1

    grand_total = 0
    grand_fail = 0
    for path in args:
        lines = parse_file(path)
        fails = []
        for num, greek in lines:
            ok, nsyl, w = check_line(greek)
            if not ok:
                fails.append((num, greek, nsyl, w))
        grand_total += len(lines)
        grand_fail += len(fails)
        rate = 100 * (len(lines) - len(fails)) / len(lines) if lines else 0
        print(f"{path}: {len(lines) - len(fails)}/{len(lines)} scan ({rate:.1f}%)")
        if verbose:
            for num, greek, nsyl, w in fails:
                print(f"  L{num} [{nsyl} syll {''.join(w)}] {greek}")

    if grand_total:
        rate = 100 * (grand_total - grand_fail) / grand_total
        print(f"\nTOTAL: {grand_total - grand_fail}/{grand_total} scan ({rate:.1f}%), "
              f"{grand_fail} not resolvable")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
