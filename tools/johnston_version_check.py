"""Version-sensitivity check for the Johnston row.

The Johnston corpus first measured (2026-08-12) derives from a May 2016
snapshot of Johnston's PDF, publicly hosted since 2016 (full source
chain with hashes in tools/corpus-manifest.txt; the text itself is
reproduced from its EPUB by tools/johnston_epub_to_text.py). Johnston
has revised the text repeatedly since it first appeared online in 2002,
and the current official PDF (VIU institutional repository, generated
2024-10-16, declaring itself public domain) revises the very passage
that produced the row's 21-word shared run. This script measures the
Claudyssey row against both versions so the difference is checkable:
the older revision gives 5-gram 2.83% and a 21-word longest run; the
2024 canonical text gives 2.43% and a 12-word longest run. Expected
hashes for both inputs are in tools/corpus-manifest.txt.

Usage: python tools/johnston_version_check.py OLD.txt CANONICAL.pdf
"""
import hashlib, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from independence_analysis import (load_public, load_private, tokenize,
                                   pair_overlap, overlap_frac, maximal_runs)

NUMWORD = ('ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|'
           'THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|SEVENTEEN|EIGHTEEN|NINETEEN|'
           'TWENTY(-(ONE|TWO|THREE|FOUR))?')


def clean_viu_pdf(path):
    """Trim the 2024 VIU PDF to translation body only: drop page numbers,
    running heads, all-caps titles, the translator's bracketed book
    summaries, and per-page footnote blocks; cut front matter and the
    floor plan/glossary back matter."""
    from pypdf import PdfReader
    out = []
    for page in PdfReader(path).pages:
        in_summary = False
        for ln in (page.extract_text() or '').split('\n'):
            s = ln.strip()
            if not s or re.fullmatch(r'\d+', s):
                continue
            if re.fullmatch(rf'BOOK ({NUMWORD})', s):
                continue
            if re.fullmatch(r"[A-Z][A-Z'’ ,:;—–-]+", s) and len(s) > 3:
                continue
            if in_summary:
                if s.endswith(']'):
                    in_summary = False
                continue
            if s.startswith('[') and not re.match(r'\[\d', s):
                if not s.endswith(']'):
                    in_summary = True
                continue
            if re.match(r'\d{1,3}[A-Z"“(‘]', s):
                break                       # footnote block: rest of page
            out.append(ln)
    text = '\n'.join(out)
    text = text[re.search(r'Muse, speak to me now of that resourceful man', text).start():]
    m = re.search(r'Possible Floor Plan', text, flags=re.I)
    return text[:m.start()] if m else text


def main():
    old_path, pdf_path = sys.argv[1], sys.argv[2]
    texts = load_public()
    cl = texts['claudyssey']
    versions = {
        'old (as measured)': load_private(
            old_path, 'Muse, speak to me now of that resourceful man'),
        'canonical 2024': tokenize(clean_viu_pdf(pdf_path)),
    }
    for name, j in versions.items():
        h = hashlib.sha256(' '.join(j).encode()).hexdigest()[:16]
        fr = [pair_overlap(cl, j, n) for n in (4, 5, 6, 8)]
        d1, d2 = overlap_frac(cl, j, 5), overlap_frac(j, cl, 5)
        runs = maximal_runs(cl, j)
        longest = max((l for _, l in runs), default=0)
        print(f'{name}: {len(j)} tokens  sha256:{h}')
        print('  claudyssey row: ' +
              ' '.join(f'{n}g {f*100:.2f}%' for n, f in zip((4, 5, 6, 8), fr)) +
              f'  (5g dir {d1*100:.2f}/{d2*100:.2f})  '
              f'runs>=12 {len(runs)}  longest {longest}')
        for i, l in sorted(runs, key=lambda r: -r[1])[:1]:
            print(f'  longest run: "{" ".join(cl[i:i+l])}"')
        print(f'  murray control 5g: {pair_overlap(texts["murray"], j, 5)*100:.2f}%')
    a, b = versions.values()
    print(f'the two Johnston versions vs each other, 5g: {pair_overlap(a, b, 5)*100:.2f}%')


if __name__ == '__main__':
    main()
