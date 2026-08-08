import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
SCRATCH = r'C:\Users\executor\AppData\Local\Temp\claude\H--My-Drive-agent-journal-odyssey\c89a8f7c-cc9c-413f-a9ba-b8f58ea70df6\scratchpad'

src = open(SCRATCH + r'\overlap.py', encoding='utf-8').read().split("print('\\n=== Claudyssey")[0]
src = src.replace("sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')", "")
exec(src)

LATT_MAP = {
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
    'laertes': 'laertes', 'aigis': 'aegis', 'grey': 'gray',
}
base_tokenize = tokenize
def tokenize2(text):
    return [LATT_MAP.get(t, t) for t in base_tokenize(text)]

lines = open(SCRATCH + r'\lattimore_pdf_raw.txt', encoding='utf-8', errors='replace').read().split('\n')
start = next(i for i, l in enumerate(lines)
             if 'Tell me, Muse, of the man of many ways' in re.sub(r'\s+', ' ', l))
end = next(i for i, l in enumerate(lines) if l.strip() == 'GLOSSARY')
body = [l for l in lines[start:end] if not l.startswith('<<<PAGE')]
raw = '\n'.join(body)
raw = raw.replace('\u00ad', '')
raw = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', raw)
latt = tokenize2(raw)
print('lattimore tokens:', len(latt))

# re-tokenize the whole panel through the same map so grey/athene etc. match fairly
texts = {k: [LATT_MAP.get(t, t) for t in v] for k, v in texts.items()}

fraw = open(SCRATCH + r'\fagles_ody_raw.txt', encoding='utf-8').read()
fraw = fraw.replace('\u00ad\n', '').replace('\u00ad', '')
fraw = re.sub(r'(\w)-\n(\w)', r'\1\2', fraw)
texts['fagles'] = tokenize2(fraw)

plines = open(SCRATCH + r'\lattimore_raw.txt', encoding='utf-8', errors='replace').read().split('\n')
pbody, started = [], False
for ln in plines:
    if not started and 'Speak to me, Muse' in ln:
        started = True
    if not started:
        continue
    if re.match(r'^\s*\d*\s*THE ODYSSEY', ln) or re.match(r'^\s*[IVXL]+\.\s', ln):
        continue
    pbody.append(ln)
praw = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', '\n'.join(pbody))
texts['palmer'] = tokenize2(praw)

cl = texts['claudyssey']

def maximal_runs(a, b, minlen):
    n = minlen
    bpos = {}
    for i in range(len(b)-n+1):
        bpos.setdefault(tuple(b[i:i+n]), []).append(i)
    runs = []
    i = 0
    while i < len(a)-n+1:
        g = tuple(a[i:i+n])
        if g in bpos:
            best_ext = 0
            for j in bpos[g]:
                k = 0
                while i+n+k < len(a) and j+n+k < len(b) and a[i+n+k] == b[j+n+k]:
                    k += 1
                best_ext = max(best_ext, k)
            runs.append((i, n+best_ext))
            i += n + best_ext
        else:
            i += 1
    return runs

print('\n=== Everyone vs Lattimore (same metric) ===')
print(f'{"text":16s} ' + ' '.join(f'{n}-gram' for n in (4,5,6,7,8)) + '   runs>=12 (>=16)  longest')
for nm in ['claudyssey', 'murray', 'butcher_lang', 'butler', 'palmer', 'fagles', 'cowper', 'pope']:
    a = texts[nm]
    fracs = [overlap(a, latt, n) for n in (4,5,6,7,8)]
    L, ex = longest_shared(a, latt)
    runs = maximal_runs(a, latt, 12)
    r16 = sum(1 for _, l in runs if l >= 16)
    print(f'{nm:16s} ' + ' '.join(f'{f*100:5.2f}%' for f in fracs) + f'   {len(runs)} ({r16})   {L}')
    if nm == 'claudyssey':
        for i, l in sorted(runs, key=lambda r: -r[1])[:4]:
            print(f'    [{l}] "' + ' '.join(a[i:i+l]) + '"')

print('\n=== Final stitching test: Claudyssey vs union of ALL EIGHT ===')
names8 = ['murray', 'butcher_lang', 'butler', 'cowper', 'pope', 'fagles', 'palmer']
for n in (4, 5, 6, 8):
    union = set(ngrams(latt, n))
    for nm in names8:
        union |= set(ngrams(texts[nm], n))
    grams = ngrams(cl, n)
    hits = sum(1 for g in grams if g in union)
    print(f'{n}-gram: {hits/len(grams)*100:5.2f}% ({100-hits/len(grams)*100:.1f}% in none of the eight)')
