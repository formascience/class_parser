"""
PDF ➜ deck ➜ slides ➜ nested bullet tree
– keeps banner filtering
– detects slide titles via biggest font size near the top
– uses REAL x‑position of the first bullet glyph for inline children
"""

import os, re, json, pdfplumber, unicodedata, string
from dotenv import load_dotenv
from typing import List, Dict, Tuple
from pydantic import BaseModel, Field
from openai import OpenAI

load_dotenv()       # OPENAI_API_KEY in .env

# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------
BULLET_CHARS = "•◦‣▪–"
BANNER_RX    = re.compile(r"^L\\d?SpS:")
INDENT_TOL   = 5                 # px – cluster threshold

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def slide_title(words, top_cutoff=150, use_biggest_font=1):
    if not words: 
        return ""
    
    # If flag is 1, find the biggest font string from all words
    if use_biggest_font == 1:
        max_size = max(w["size"] for w in words)
        biggest_font_words = sorted([w for w in words 
                                   if abs(w["size"] - max_size) < 0.5],
                                  key=lambda w: w["x0"])
        return " ".join(w["text"] for w in biggest_font_words)
    
    # Original logic for when flag is not 1
    top_words = [w for w in words if w["top"] < top_cutoff]
    if not top_words: 
        return ""
    max_size = max(w["size"] for w in top_words)
    title_words = sorted([w for w in top_words
                          if abs(w["size"] - max_size) < 0.5],
                         key=lambda w: w["x0"])
    return " ".join(w["text"] for w in title_words)

def first_bullet_x(row_words):
    """Find x-position of first bullet character in row"""
    for w in row_words:
        if any(c in w["text"] for c in BULLET_CHARS):
            return w["x0"]
    return None

# ----------------------------------------------------------------------
# 1. PDF ➜ deck
# ----------------------------------------------------------------------
def extract_lines(pdf_path: str):
    deck, banner_hits = [], {}

    with pdfplumber.open(pdf_path) as pdf:
        for idx, page in enumerate(pdf.pages, 1):
            words = page.extract_words(use_text_flow=True, extra_attrs=["size"])
            rows: Dict[float, List[dict]] = {}
            for w in words:
                txt = w["text"].strip()
                if BANNER_RX.match(txt):
                    banner_hits[txt] = banner_hits.get(txt, 0) + 1
                    continue
                y = round(w["top"], 1)
                rows.setdefault(y, []).append(w)

            lines = []
            for y in sorted(rows):
                row_words = sorted(rows[y], key=lambda w: w["x0"])
                x0 = row_words[0]["x0"]
                txt = " ".join(w["text"] for w in row_words)
                txt = re.sub(rf"\s*{idx}\s*$", "", txt).strip()
                if txt:
                    lines.append((x0, txt, row_words))   # keep row_words

            deck.append({
                "page":  idx,
                "title": slide_title(words),
                "lines": lines                          # (x0, txt, row_words)
            })

    banner_texts = {t for t,c in banner_hits.items() if c/len(deck) >= 0.8}
    for sl in deck:
        sl["lines"] = [(x,t,rw) for x,t,rw in sl["lines"] if t not in banner_texts]

    return deck

# ----------------------------------------------------------------------
# 2. deck ➜ slides  (explode inline bullets)
# ----------------------------------------------------------------------
def explode_line(x0, line, row_words, page_idx):
    """
    If the row is "Parent • child • child", use x‑pos of the first bullet
    glyph for all children so that INTRO and "Le génome humain" share the
    SAME indent.
    """
    line = re.sub(rf"\s*{page_idx}\s*$", "", line).strip()
    if "•" not in line:
        return [{"indent": x0, "text": line}]

    head, tail = line.split("•", 1)
    head = head.strip()
    out  = []

    # parent node (if any)
    if head:
        out.append({"indent": x0, "text": head})

    bullet_x = first_bullet_x(row_words) or x0
    children = [frag.strip() for frag in tail.split("•") if frag.strip()]
    out.extend({"indent": bullet_x, "text": c} for c in children)
    return out

def split_bullets(deck):
    slides = []
    for sl in deck:
        bullets = []
        for x, txt, row in sl["lines"]:
            bullets.extend(explode_line(x, txt, row, sl["page"]))
        slides.append({"page": sl["page"], "title": sl["title"], "bullets": bullets})
    return slides

# ----------------------------------------------------------------------
# 3. bullets ➜ nested tree
# ----------------------------------------------------------------------
def bullet_tree(slide: dict, tol=INDENT_TOL):
    bullets = slide["bullets"]
    if not bullets:
        return {"page": slide["page"], "title": slide["title"], "tree": []}

    indents = sorted({b["indent"] for b in bullets})
    # cluster indents
    groups, cur = [], [indents[0]]
    for x in indents[1:]:
        if x - cur[-1] <= tol: cur.append(x)
        else: groups.append(cur); cur=[x]
    groups.append(cur)
    depth = {x:i for i,g in enumerate(groups) for x in g}

    root, stack = [], []
    for b in bullets:
        lvl = depth[b["indent"]]
        node = {"text": b["text"], "children": []}
        while len(stack) > lvl: stack.pop()
        (root if not stack else stack[-1]["children"]).append(node)
        stack.append(node)

    return {"page": slide["page"], "title": slide["title"], "tree": root}

# ----------------------------------------------------------------------
# demo run
# ----------------------------------------------------------------------
PDF = "./volume/slides/cours_1.pdf"      # adjust path

deck   = extract_lines(PDF)
slides = split_bullets(deck)
trees  = [bullet_tree(sl) for sl in slides]

# print the first two slide trees for inspection
from pprint import pprint
pprint(trees, width=120, sort_dicts=False)
