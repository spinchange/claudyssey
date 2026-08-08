import re, glob, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
src = open(r'C:\Users\executor\AppData\Local\Temp\claude\H--My-Drive-agent-journal-odyssey\c89a8f7c-cc9c-413f-a9ba-b8f58ea70df6\scratchpad\overlap.py', encoding='utf-8').read().split("print('\\n=== Claudyssey")[0]
src = src.replace("sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')", "")
exec(src)

def maximal_runs(a, b, minlen):
    """count maximal shared contiguous runs of >= minlen tokens (greedy from seed matches)"""
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

cl = texts['claudyssey']
for label, a, b in [('claudyssey vs murray', cl, texts['murray']),
                    ('claudyssey vs butcher_lang', cl, texts['butcher_lang']),
                    ('CONTROL butcher_lang vs murray', texts['butcher_lang'], texts['murray']),
                    ('CONTROL butler vs murray', texts['butler'], texts['murray'])]:
    runs = maximal_runs(a, b, 12)
    print(f'\n{label}: maximal shared runs >=12 tokens: {len(runs)}  '
          f'(>=16: {sum(1 for _,l in runs if l>=16)}, >=20: {sum(1 for _,l in runs if l>=20)})')
    for i, l in sorted(runs, key=lambda r: -r[1])[:4]:
        print(f'  [{l} tokens] "' + ' '.join(a[i:i+l]) + '"')
