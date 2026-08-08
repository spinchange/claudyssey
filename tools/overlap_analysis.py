import re, glob, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SCRATCH = r'C:\Users\executor\AppData\Local\Temp\claude\H--My-Drive-agent-journal-odyssey\c89a8f7c-cc9c-413f-a9ba-b8f58ea70df6\scratchpad'
REPO = r'H:\My Drive\agent-journal\odyssey'

NAME_MAP = {
    'ulysses': 'odysseus', 'jove': 'zeus', 'jupiter': 'zeus', 'minerva': 'athena',
    'juno': 'hera', 'neptune': 'poseidon', 'mercury': 'hermes', 'venus': 'aphrodite',
    'vulcan': 'hephaestus', 'mars': 'ares', 'diana': 'artemis', 'proserpine': 'persephone',
    'aurora': 'dawn', 'sol': 'helios', 'pallas': 'athena',
}

def tokenize(text):
    text = text.lower()
    text = re.sub(r'[\u2018\u2019]', "'", text)
    text = re.sub(r'[\u201c\u201d]', '"', text)
    text = re.sub(r'[\u2014\u2013]', ' ', text)
    text = re.sub(r"'s\b", '', text)          # drop possessives: troy's -> troy
    text = re.sub(r'[^a-z\s]', ' ', text)
    toks = text.split()
    return [NAME_MAP.get(t, t) for t in toks]

def load_claudyssey():
    parts = []
    for f in sorted(glob.glob(REPO + r'\translation\book-*.md')):
        for line in open(f, encoding='utf-8'):
            s = line.strip()
            if not s or s.startswith('#') or s.startswith('[^'):
                continue
            if s.startswith('*') and s.endswith('*'):
                continue
            s = re.sub(r'^\d+\s+', '', s)          # line numbers
            s = re.sub(r'\[\^[^\]]+\]', '', s)     # footnote refs
            parts.append(s)
    return ' '.join(parts)

def load_gutenberg(path):
    raw = open(path, encoding='utf-8', errors='replace').read()
    m = re.search(r'\*\*\* ?START OF.*?\*\*\*', raw)
    if m: raw = raw[m.end():]
    m = re.search(r'\*\*\* ?END OF', raw)
    if m: raw = raw[:m.start()]
    return raw

texts = {}
texts['claudyssey'] = tokenize(load_claudyssey())
texts['murray'] = tokenize(open(SCRATCH + r'\murray.txt', encoding='utf-8', errors='replace').read())
texts['butler'] = tokenize(load_gutenberg(SCRATCH + r'\butler.txt'))
texts['butcher_lang'] = tokenize(load_gutenberg(SCRATCH + r'\butcher_lang.txt'))
texts['cowper'] = tokenize(load_gutenberg(SCRATCH + r'\cowper.txt'))
texts['pope'] = tokenize(load_gutenberg(SCRATCH + r'\pope.txt'))

for k, v in texts.items():
    print(f'{k}: {len(v)} tokens')

def ngrams(toks, n):
    return [tuple(toks[i:i+n]) for i in range(len(toks)-n+1)]

def overlap(a, b, n):
    """fraction of A's positional n-grams found anywhere in B"""
    bset = set(ngrams(b, n))
    grams = ngrams(a, n)
    hits = sum(1 for g in grams if g in bset)
    return hits / len(grams)

def longest_shared(a, b, lo=4, hi=60):
    """binary search longest common contiguous token run; return length and examples"""
    def matches_at(n):
        bset = set(ngrams(b, n))
        return [i for i, g in enumerate(ngrams(a, n)) if g in bset]
    best, best_idx = 0, []
    while lo <= hi:
        mid = (lo + hi) // 2
        m = matches_at(mid)
        if m:
            best, best_idx = mid, m
            lo = mid + 1
        else:
            hi = mid - 1
    examples = []
    seen = set()
    for i in best_idx[:5]:
        s = ' '.join(a[i:i+best])
        if s not in seen:
            seen.add(s)
            examples.append(s)
    return best, examples

names = ['murray', 'butler', 'butcher_lang', 'cowper', 'pope']
cl = texts['claudyssey']

print('\n=== Claudyssey vs each human translation ===')
print(f'{"pair":34s} ' + ' '.join(f'{n}-gram' for n in (4,5,6,7,8)) + '   longest')
for nm in names:
    t = texts[nm]
    fracs = [overlap(cl, t, n) for n in (4,5,6,7,8)]
    L, ex = longest_shared(cl, t)
    print(f'claudyssey vs {nm:20s} ' + ' '.join(f'{f*100:5.2f}%' for f in fracs) + f'   {L}')
    for e in ex[:2]:
        print(f'    longest shared: "{e}"')

print('\n=== Claudyssey vs UNION of all five (the "stitching" test) ===')
for n in (4,5,6,7,8):
    union = set()
    for nm in names:
        union |= set(ngrams(texts[nm], n))
    grams = ngrams(cl, n)
    hits = sum(1 for g in grams if g in union)
    print(f'{n}-gram: {hits/len(grams)*100:5.2f}%')

print('\n=== Human vs human controls (same metric) ===')
controls = [('butcher_lang','murray'), ('butler','murray'), ('butler','butcher_lang'),
            ('cowper','pope'), ('cowper','murray')]
print(f'{"pair":34s} ' + ' '.join(f'{n}-gram' for n in (4,5,6,7,8)) + '   longest')
for a, b in controls:
    fracs = [overlap(texts[a], texts[b], n) for n in (4,5,6,7,8)]
    L, ex = longest_shared(texts[a], texts[b])
    print(f'{a} vs {b:20s} ' + ' '.join(f'{f*100:5.2f}%' for f in fracs) + f'   {L}')
    for e in ex[:1]:
        print(f'    longest shared: "{e}"')
