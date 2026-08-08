"""Overlap analysis behind docs/independence.html.

Measures n-gram overlap and verbatim shared runs between this translation
and prior English Odysseys, with every human-vs-human pairing as control,
a union ("stitching") test, and a synthetic splice as positive control.

Public-domain texts are downloaded on first run into corpus/ (Gutenberg,
Scaife/Perseus, archive.org) and trimmed to translation body only —
prefaces, arguments, and footnotes removed. Lattimore and Fagles are in
copyright: supply private copies via --lattimore / --fagles (PDF or txt);
without them the script reproduces the public-domain subtable.

Usage:  python tools/independence_analysis.py [--lattimore PATH] [--fagles PATH]
"""
import argparse, glob, hashlib, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, 'corpus')

SOURCES = {
    'butler':       'https://www.gutenberg.org/cache/epub/1727/pg1727.txt',
    'butcher_lang': 'https://www.gutenberg.org/cache/epub/1728/pg1728.txt',
    'pope':         'https://www.gutenberg.org/cache/epub/3160/pg3160.txt',
    'cowper':       'https://www.gutenberg.org/cache/epub/24269/pg24269.txt',
    'palmer':       'https://archive.org/download/odysseyhomer12homegoog/odysseyhomer12homegoog_djvu.txt',
}
MURRAY_URN = ('https://scaife.perseus.org/library/passage/'
              'urn:cts:greekLit:tlg0012.tlg002.perseus-eng3:{book}/text/')

# Latin/Greek name traditions and orthography normalized so spelling
# conventions cannot mask (or fake) overlap.
NAME_MAP = {
    'ulysses': 'odysseus', 'jove': 'zeus', 'jupiter': 'zeus', 'minerva': 'athena',
    'juno': 'hera', 'neptune': 'poseidon', 'mercury': 'hermes', 'venus': 'aphrodite',
    'vulcan': 'hephaestus', 'mars': 'ares', 'diana': 'artemis',
    'proserpine': 'persephone', 'aurora': 'dawn', 'sol': 'helios', 'pallas': 'athena',
    'telemachos': 'telemachus', 'ithaka': 'ithaca', 'kalypso': 'calypso',
    'kirke': 'circe', 'kyklops': 'cyclops', 'kyklopes': 'cyclopes',
    'achaians': 'achaeans', 'achaian': 'achaean', 'aigisthos': 'aegisthus',
    'alkinoos': 'alcinous', 'nausikaa': 'nausicaa', 'menelaos': 'menelaus',
    'peisistratos': 'pisistratus', 'eumaios': 'eumaeus', 'teiresias': 'tiresias',
    'phaiakians': 'phaeacians', 'phaiakian': 'phaeacian', 'aiolos': 'aeolus',
    'athene': 'athena', 'herakles': 'heracles', 'klytaimestra': 'clytemnestra',
    'antinoos': 'antinous', 'eurymachos': 'eurymachus', 'amphinomos': 'amphinomus',
    'melanthios': 'melanthius', 'eurykleia': 'eurycleia', 'polyphemos': 'polyphemus',
    'demodokos': 'demodocus', 'achilleus': 'achilles', 'patroklos': 'patroclus',
    'hektor': 'hector', 'apollon': 'apollo', 'hephaistos': 'hephaestus',
    'olympos': 'olympus', 'parnassos': 'parnassus', 'krete': 'crete',
    'lakedaimon': 'lacedaemon', 'okeanos': 'oceanus', 'kronos': 'cronos',
    'skylla': 'scylla', 'kharybdis': 'charybdis', 'ikarios': 'icarius',
    'aigis': 'aegis', 'grey': 'gray',
}


def fetch(name, url):
    os.makedirs(CORPUS, exist_ok=True)
    path = os.path.join(CORPUS, name + '.txt')
    if not os.path.exists(path):
        print(f'downloading {name} …', file=sys.stderr)
        req = urllib.request.Request(url, headers={'User-Agent': 'claudyssey-independence-analysis'})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req) as r:
                    data = r.read()
                break
            except Exception:
                if attempt == 3:
                    raise
                import time
                time.sleep(5 * (attempt + 1))
        open(path, 'wb').write(data)
    return open(path, encoding='utf-8', errors='replace').read()


def tokenize(text):
    text = text.replace('­', '')
    text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)   # hyphen line-breaks
    text = text.lower()
    text = re.sub(r'[‘’]', "'", text)
    text = re.sub(r"'s\b", '', text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    return [NAME_MAP.get(t, t) for t in text.split()]


def strip_gutenberg(raw):
    m = re.search(r'\*\*\* ?START OF.*?\*\*\*', raw)
    if m: raw = raw[m.end():]
    m = re.search(r'\*\*\* ?END OF', raw)
    if m: raw = raw[:m.start()]
    return raw


def body_between(lines, start_pred, end_pred=None):
    out, started = [], False
    for ln in lines:
        if not started:
            if start_pred(ln):
                started = True
            else:
                continue
        if end_pred and end_pred(ln):
            break
        out.append(ln)
    return out


def load_claudyssey():
    parts = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'translation', 'book-*.md'))):
        for line in open(f, encoding='utf-8'):
            s = line.strip()
            if not s or s.startswith('#') or s.startswith('[^'):
                continue
            if s.startswith('*') and s.endswith('*'):
                continue
            s = re.sub(r'^\d+\s+', '', s)
            s = re.sub(r'\[\^[^\]]+\]', '', s)
            parts.append(s)
    return ' '.join(parts)


def load_public():
    texts = {'claudyssey': tokenize(load_claudyssey())}

    murray = []
    for b in range(1, 25):
        murray.append(fetch(f'murray_{b:02d}', MURRAY_URN.format(book=b)))
    texts['murray'] = tokenize('\n'.join(murray))

    # Butler: preface (which QUOTES Butcher & Lang's proem — see the page's
    # "what copying looks like" section) removed; footnotes removed.
    lines = strip_gutenberg(fetch('butler', SOURCES['butler'])).split('\n')
    body = body_between(lines,
                        lambda l: 'Tell me, O Muse, of that ingenious hero' in l,
                        lambda l: l.strip() == 'FOOTNOTES:')
    texts['butler'] = tokenize('\n'.join(body))

    lines = strip_gutenberg(fetch('butcher_lang', SOURCES['butcher_lang'])).split('\n')
    body = body_between(lines,
                        lambda l: 'Tell me, Muse, of that man, so ready at need' in l)
    texts['butcher_lang'] = tokenize('\n'.join(body))

    # Cowper: editor front matter removed; per-book FOOTNOTES blocks removed
    # (his ARGUMENT summaries retained — a few hundred words, noted on page).
    lines = strip_gutenberg(fetch('cowper', SOURCES['cowper'])).split('\n')
    body, started, in_notes = [], False, False
    for ln in lines:
        if not started:
            if 'Muse make the man thy theme' in ln:
                started = True
            else:
                continue
        if ln.strip() == 'FOOTNOTES:':
            in_notes = True
        elif in_notes and re.match(r'^BOOK [XVI]+', ln.strip()):
            in_notes = False
        if not in_notes:
            body.append(ln)
    texts['cowper'] = tokenize('\n'.join(body))

    lines = strip_gutenberg(fetch('pope', SOURCES['pope'])).split('\n')
    body = body_between(lines,
                        lambda l: 'The man for wisdom' in l)
    texts['pope'] = tokenize('\n'.join(body))

    # Palmer 1891, from a Google/archive.org scan (item mislabeled "Lattimore"
    # in archive metadata; text is unmistakably Palmer). OCR noise slightly
    # depresses every Palmer pairing equally. Running page headers removed.
    lines = fetch('palmer', SOURCES['palmer']).split('\n')
    body = [l for l in body_between(lines, lambda l: 'Speak to me, Muse' in l)
            if not re.match(r'^\s*\d*\s*THE ODYSSEY', l)
            and not re.match(r'^\s*[IVXL]+\.\s', l)]
    texts['palmer'] = tokenize('\n'.join(body))
    return texts


def load_private(path, start_marker, end_marker=None):
    if path.lower().endswith('.pdf'):
        from pypdf import PdfReader
        raw = '\n'.join((p.extract_text() or '') for p in PdfReader(path).pages)
    else:
        raw = open(path, encoding='utf-8', errors='replace').read()
    lines = raw.split('\n')
    norm = lambda l: re.sub(r'\s+', ' ', l)
    body = body_between(lines,
                        lambda l: start_marker in norm(l),
                        (lambda l: norm(l).strip() == end_marker) if end_marker else None)
    return tokenize('\n'.join(body))


def ngrams(toks, n):
    return [tuple(toks[i:i+n]) for i in range(len(toks)-n+1)]


def overlap_frac(a, b, n):
    bset = set(ngrams(b, n))
    grams = ngrams(a, n)
    return sum(1 for g in grams if g in bset) / len(grams)


def pair_overlap(a, b, n):
    """symmetric: the larger of the two directional fractions"""
    return max(overlap_frac(a, b, n), overlap_frac(b, a, n))


def maximal_runs(a, b, minlen=12):
    n = minlen
    bpos = {}
    for i in range(len(b)-n+1):
        bpos.setdefault(tuple(b[i:i+n]), []).append(i)
    runs, i = [], 0
    while i < len(a)-n+1:
        g = tuple(a[i:i+n])
        if g in bpos:
            ext = 0
            for j in bpos[g]:
                k = 0
                while i+n+k < len(a) and j+n+k < len(b) and a[i+n+k] == b[j+n+k]:
                    k += 1
                ext = max(ext, k)
            runs.append((i, n+ext))
            i += n + ext
        else:
            i += 1
    return runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lattimore', help='path to a private copy (pdf or txt)')
    ap.add_argument('--fagles', help='path to a private copy (pdf or txt)')
    args = ap.parse_args()

    texts = load_public()
    if args.lattimore:
        texts['lattimore'] = load_private(
            args.lattimore, 'Tell me, Muse, of the man of many ways', 'GLOSSARY')
    if args.fagles:
        texts['fagles'] = load_private(
            args.fagles, 'Sing to me of the man, Muse')

    print('corpus (translation body only, normalized):')
    for k, v in texts.items():
        h = hashlib.sha256(' '.join(v).encode()).hexdigest()[:16]
        print(f'  {k:14s} {len(v):7d} tokens   sha256:{h}')

    humans = [k for k in texts if k != 'claudyssey']
    cl = texts['claudyssey']

    print('\nclaudyssey vs each (directional-max):')
    print(f'  {"text":14s} {"4g":>7s} {"5g":>7s} {"6g":>7s} {"8g":>7s} '
          f'{"runs>=12":>9s} {"runs>=16":>9s} {"longest":>8s}')
    for nm in humans:
        t = texts[nm]
        fr = [pair_overlap(cl, t, n) for n in (4, 5, 6, 8)]
        runs = maximal_runs(cl, t)
        longest = max((l for _, l in runs), default=0)
        print(f'  {nm:14s} ' + ' '.join(f'{f*100:6.2f}%' for f in fr) +
              f' {len(runs):9d} {sum(1 for _, l in runs if l >= 16):9d} {longest:8d}')
        for i, l in sorted(runs, key=lambda r: -r[1])[:1]:
            print(f'      longest: "{" ".join(cl[i:i+l])}"')

    print('\nall human-vs-human pairs, 5-gram (directional-max), sorted:')
    hh = []
    for i, a in enumerate(humans):
        for b in humans[i+1:]:
            hh.append((pair_overlap(texts[a], texts[b], 5), a, b))
    for f, a, b in sorted(hh, reverse=True):
        print(f'  {f*100:6.2f}%  {a} vs {b}')

    print('\nunion ("stitching") test — claudyssey n-grams found in ANY prior text:')
    for n in (4, 5, 6, 8):
        union = set()
        for nm in humans:
            union |= set(ngrams(texts[nm], n))
        grams = ngrams(cl, n)
        hits = sum(1 for g in grams if g in union)
        print(f'  {n}-gram: {hits/len(grams)*100:5.2f}% found, '
              f'{100-hits/len(grams)*100:.1f}% in none')

    # positive control: a deliberate verbatim splice, alternating 12-token
    # chunks from the three most literal texts — what "stitching" would score
    donors = [texts[k] for k in ('murray', 'butcher_lang', 'lattimore')
              if k in texts][:3]
    if len(donors) >= 2:
        splice, pos = [], [0]*len(donors)
        while len(splice) < len(cl):
            for d, t in enumerate(donors):
                splice.extend(t[pos[d]:pos[d]+12])
                pos[d] += 12
        splice = splice[:len(cl)]
        union5 = set()
        for nm in humans:
            union5 |= set(ngrams(texts[nm], 5))
        grams = ngrams(splice, 5)
        hits = sum(1 for g in grams if g in union5)
        print(f'\npositive control — verbatim splice of {len(donors)} texts, '
              f'12-token chunks:')
        print(f'  5-gram vs union: {hits/len(grams)*100:5.2f}% found '
              f'(claudyssey: see above)')


if __name__ == '__main__':
    main()
