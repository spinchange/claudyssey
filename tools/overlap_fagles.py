import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
SCRATCH = r'C:\Users\executor\AppData\Local\Temp\claude\H--My-Drive-agent-journal-odyssey\c89a8f7c-cc9c-413f-a9ba-b8f58ea70df6\scratchpad'

src = open(SCRATCH + r'\overlap.py', encoding='utf-8').read().split("print('\\n=== Claudyssey")[0]
src = src.replace("sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')", "")
exec(src)

raw = open(SCRATCH + r'\fagles_ody_raw.txt', encoding='utf-8').read()
raw = raw.replace('\u00ad\n', '').replace('\u00ad', '')
raw = re.sub(r'(\w)-\n(\w)', r'\1\2', raw)
fag = tokenize(raw)
texts['fagles'] = fag
print('fagles_odyssey tokens:', len(fag))

cl = texts['claudyssey']
names = ['murray', 'butcher_lang', 'butler', 'cowper', 'pope']

print('\n=== Everyone vs Fagles Odyssey (same metric, same poem) ===')
print(f'{"pair":30s} ' + ' '.join(f'{n}-gram' for n in (4,5,6,7,8)) + '   longest')
for nm in ['claudyssey'] + names:
    a = texts[nm]
    fracs = [overlap(a, fag, n) for n in (4,5,6,7,8)]
    L, ex = longest_shared(a, fag)
    print(f'{nm:30s} ' + ' '.join(f'{f*100:5.2f}%' for f in fracs) + f'   {L}')
    for e in ex[:2]:
        print(f'    longest shared: "{e}"')

print('\n=== Stitching test: Claudyssey vs union of all six ===')
for n in (4,5,6,8):
    union = set()
    for nm in names + ['fagles']:
        union |= set(ngrams(texts[nm], n))
    grams = ngrams(cl, n)
    hits = sum(1 for g in grams if g in union)
    print(f'{n}-gram: {hits/len(grams)*100:5.2f}%  ({100-hits/len(grams)*100:.1f}% in none)')

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

print('\n=== Long shared runs vs Fagles Odyssey ===')
for nm in ['claudyssey', 'butcher_lang', 'murray', 'butler']:
    runs = maximal_runs(texts[nm], fag, 10)
    print(f'{nm}: runs >=10: {len(runs)}  (>=12: {sum(1 for _,l in runs if l>=12)}, >=16: {sum(1 for _,l in runs if l>=16)})')
    for i, l in sorted(runs, key=lambda r: -r[1])[:3]:
        print(f'  [{l}] "' + ' '.join(texts[nm][i:i+l]) + '"')
