"""Reproduce the measured Johnston corpus from its EPUB, byte for byte.

Provenance chain for the Johnston row (established 2026-08-12, fourth
review): Johnston's May 2016 PDF, publicly hosted since 2016 at
https://bootthanoo.github.io/iliadodyssey/The%20Odyssey/Full%20Book/theodyssey.pdf
(sha256 b2fef533...c239769, in the manifest), was converted locally to a
structured EPUB (one XHTML per book, apparatus separated from verse);
this script extracts the verse from that EPUB and reproduces
corpus/johnston.txt exactly (sha256 fb627016...bb67d1). The PDF-to-EPUB
step is a local conversion and is documented by hash rather than
reproduced; everything downstream of the EPUB is reproducible here.

Usage: python tools/johnston_epub_to_text.py THEODYSSEY.epub OUT.txt
"""
import html, re, sys, zipfile


def extract(epub_path):
    z = zipfile.ZipFile(epub_path)
    books = []
    for n in range(1, 25):
        x = z.read(f'OEBPS/book{n:02d}.xhtml').decode('utf-8')
        lines = re.findall(r'<span class="line-text">(.*?)</span></div>', x, re.S)
        lines = [re.sub(r'<sup class="note-marker">.*?</sup>', '', l) for l in lines]
        lines = [html.unescape(re.sub(r'<[^>]+>', '', l)) for l in lines]
        books.append('\n'.join(lines))
    return '\n\n'.join(books) + '\n'


if __name__ == '__main__':
    text = extract(sys.argv[1])
    with open(sys.argv[2], 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    import hashlib
    print(f'{len(text.splitlines())} lines, sha256:'
          f'{hashlib.sha256(text.encode("utf-8")).hexdigest()}')
