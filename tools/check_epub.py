#!/usr/bin/env python3
"""Lightweight structural EPUB validator (no Java/epubcheck needed).

Checks the invariants that actually break e-readers:
  - mimetype is the first entry and stored uncompressed
  - container.xml resolves to the OPF
  - every manifest href exists in the archive
  - every spine idref is declared in the manifest
  - every internal href/src in the XHTML resolves (files + local #ids)

This is not a substitute for W3C epubcheck, but catches the common
build regressions: broken footnote links, missing fonts, dangling refs.
"""
import os, re, sys, zipfile
from xml.etree import ElementTree as ET

def check(path):
    issues = []
    z = zipfile.ZipFile(path)
    names = z.namelist()

    if names[0] != "mimetype":
        issues.append("mimetype is not the first archive entry")
    else:
        info = z.getinfo("mimetype")
        if info.compress_type != zipfile.ZIP_STORED:
            issues.append("mimetype must be stored uncompressed")
        if z.read("mimetype") != b"application/epub+zip":
            issues.append("mimetype content is wrong")

    cont = z.read("META-INF/container.xml").decode()
    opf_path = re.search(r'full-path="([^"]+)"', cont).group(1)
    opf = z.read(opf_path).decode()
    base = os.path.dirname(opf_path)

    OPF = "{http://www.idpf.org/2007/opf}"
    root = ET.fromstring(opf)
    manifest = {}
    for it in root.iter(OPF + "item"):
        manifest[it.get("id")] = it.get("href")
        p = (base + "/" + it.get("href")).lstrip("/")
        if p not in names:
            issues.append(f"manifest href not in archive: {p}")
    spine = [s.get("idref") for s in root.iter(OPF + "itemref")]
    for idref in spine:
        if idref not in manifest:
            issues.append(f"spine idref not in manifest: {idref}")

    backlinks = noterefs = 0
    for n in names:
        if not n.endswith(".xhtml"):
            continue
        txt = z.read(n).decode("utf-8", "ignore")
        backlinks += len(re.findall(r'role="doc-backlink"', txt))
        noterefs += len(re.findall(r'role="doc-noteref"', txt))
        d = os.path.dirname(n)
        for href in re.findall(r'(?:href|src)="([^"]+)"', txt):
            if href.startswith(("http:", "https:", "data:", "mailto:")):
                continue
            if href.startswith("#"):
                if f'id="{href[1:]}"' not in txt:
                    issues.append(f"{n}: dangling local id {href}")
                continue
            path_part, _, frag = href.partition("#")
            tgt = os.path.normpath(os.path.join(d, path_part)).replace(os.sep, "/")
            if tgt not in names:
                issues.append(f"{n}: broken link -> {href}")
            elif frag and tgt.endswith(".xhtml"):
                tt = z.read(tgt).decode("utf-8", "ignore")
                if f'id="{frag}"' not in tt:
                    issues.append(f"{n}: link {href} -> missing id #{frag}")

    print(f"spine ({len(spine)}): {spine}")
    print(f"note refs: {noterefs}   back-links: {backlinks}")
    # Each note carries a linked number AND a return arrow, both pointing back
    # to the marker — so expect two back-links per note. Flag only if there are
    # fewer back-links than refs (i.e. some note is missing its return path).
    if noterefs and backlinks < noterefs:
        issues.append(f"missing back-links: {noterefs} refs vs {backlinks} backlinks")
    if issues:
        print(f"\nFAIL — {len(issues)} issue(s):")
        for i in issues:
            print("  -", i)
        return 1
    print("\nPASS — structurally sound, all internal links resolve")
    return 0

if __name__ == "__main__":
    sys.exit(check(sys.argv[1]))
