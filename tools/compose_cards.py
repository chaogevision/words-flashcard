#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 08 reference composer (deterministic, target-first layout).

Why this tool exists
--------------------
Prompt rules alone do not stop the two most common production defects:
  * label cards pinned to fixed perimeter slots, which produces very long
    connectors that cut across the illustration;
  * teaching text measured from generated pixels instead of the curriculum.

This composer makes the layout *target-first* and enforces a connector length
ceiling mechanically. It never reads text from the base illustration.

Usage
-----
    python3 tools/compose_cards.py run_config.json [--only CARD_ID ...]

`run_config.json`
-----------------
{
  "canvas": {"width": 2048, "height": 0},
  "margin": 72,
  "fonts": {
    "english": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "ipa": "/Library/Fonts/Arial Unicode.ttf",
    "chinese": "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "chinese_index": 0
  },
  "ceiling": {"soft": 0.15, "hard": 0.26},
  "cards": [
    {
      "card_id": "G3A-U1-C01",
      "base": "base/g3a-u1-c01.png",
      "out": "cards/g3a-u1-c01.png",
      "crop_bottom_px": 116,
      "labels": [
        {"term": "eye", "english": "eye", "ipa": "/aɪ/", "chinese": "眼睛",
         "mapping_mode": "direct_anchor", "connector_policy": "required",
         "anchor": {"x": 0.445, "y": 0.468}}
      ]
    }
  ]
}

`"height": 0` means "derive the canvas height from the cropped base so the
illustration is never letterboxed or stretched".
"""
import argparse
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DEBUG = bool(os.environ.get("FLASHCARD_DEBUG"))

DEFAULTS = {
    "fonts": {
        "english": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "ipa": "/Library/Fonts/Arial Unicode.ttf",
        "chinese": "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "chinese_index": 0,
    },
    # design_tokens.json @ 1536-wide reference canvas
    "tokens": {
        "en_size": (76, 54),
        "ipa_size": (42, 28),
        "cn_size": (42, 28),
        "card_fill": (255, 253, 249),
        "en_color": (14, 43, 109),
        "ipa_color": (86, 103, 127),
        "cn_color": (51, 51, 51),
        "connector": (183, 198, 216),
        "dot": (161, 180, 202),
        "radius_ratio": 0.018,
        "pad_x_ratio": 0.024,
        "pad_y_ratio": 0.016,
    },
    "ceiling": {"soft": 0.15, "hard": 0.26},
    "margin_ratio": 0.035,
    "max_label_width_ratio": 0.34,
    "reference_width": 1536,
}

FIRST_EDGE = {
    "direct_anchor": "required",
    "action_anchor": "optional",
    "relation_anchor": "optional",
    "scene_state": "none",
    "dialogue_phrase": "none",
    "timeline_segment": "none",
    "comparison_zone": "none",
}


# ---------------------------------------------------------------- text helpers
def text_w(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0]


def wrap_latin(draw, text, font, max_w):
    words = text.split()
    if len(words) == 1:
        return [text]
    lines, cur = [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if text_w(draw, cand, font) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def wrap_cjk(draw, text, font, max_w):
    if text_w(draw, text, font) <= max_w:
        return [text]
    lines, cur = [], ""
    for ch in text:
        cand = cur + ch
        if text_w(draw, cand, font) <= max_w:
            cur = cand
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def fit_latin(draw, text, path, max_w, hi, lo):
    size = hi
    while size > lo:
        f = ImageFont.truetype(path, size)
        if max(text_w(draw, l, f) for l in wrap_latin(draw, text, f, max_w)) <= max_w:
            return f
        size -= 2
    return ImageFont.truetype(path, lo)


def fit_size(draw, text, path, max_w, hi, lo, index, wrap, max_lines):
    """CJK/IPA: shrink a little, then wrap by line budget instead of shrinking further."""
    size = hi
    while size >= lo:
        f = ImageFont.truetype(path, size, index=index) if index is not None else ImageFont.truetype(path, size)
        lines = wrap(draw, text, f, max_w)
        if len(lines) <= max_lines and max(text_w(draw, l, f) for l in lines) <= max_w:
            return f, lines
        size -= 2
    f = ImageFont.truetype(path, lo, index=index) if index is not None else ImageFont.truetype(path, lo)
    return f, wrap(draw, text, f, max_w)


# ---------------------------------------------------------------- label layout
def make_label(draw, label, max_w, scale, tok):
    pad_x, pad_y = int(tok["pad_x_ratio"] * 2048 * scale), int(tok["pad_y_ratio"] * 2048 * scale)
    inner = max_w - pad_x * 2
    f_en = fit_latin(draw, label["english"], DEFAULTS["fonts"]["english"],
                     inner, int(tok["en_size"][0] * scale), int(tok["en_size"][1] * scale))
    en = wrap_latin(draw, label["english"], f_en, inner)
    f_ip, ip = fit_size(draw, label.get("ipa") or "", DEFAULTS["fonts"]["ipa"], inner,
                        int(tok["ipa_size"][0] * scale), int(tok["ipa_size"][1] * scale),
                        None, wrap_latin, 2)
    return {
        "pad_x": pad_x, "pad_y": pad_y,
        "en": en, "f_en": f_en, "en_lh": int(f_en.size * 1.16),
        "ip": ip if label.get("ipa") else [], "f_ip": f_ip, "ip_lh": int(f_ip.size * 1.34),
        "max_w": max_w,
        "_inner": inner,
    }


def finish_cn(draw, label, lb, scale, tok, cn_path, cn_index):
    inner = lb["_inner"]
    f, lines = fit_size(draw, label["chinese"], cn_path, inner,
                        int(tok["cn_size"][0] * scale), int(tok["cn_size"][1] * scale),
                        cn_index, wrap_cjk, 3)
    lb["cn"], lb["f_cn"], lb["cn_lh"] = lines, f, int(f.size * 1.34)
    content = max(max(text_w(draw, l, lb["f_en"]) for l in lb["en"]),
                  max([text_w(draw, l, lb["f_ip"]) for l in lb["ip"]] or [0]),
                  max(text_w(draw, l, lb["f_cn"]) for l in lb["cn"]))
    lb["w"] = min(lb["max_w"], content + lb["pad_x"] * 2)
    lb["h"] = (lb["pad_y"] * 2 + lb["en_lh"] * len(lb["en"]) + 8
               + lb["ip_lh"] * len(lb["ip"]) + 4 + lb["cn_lh"] * len(lb["cn"]))
    return lb


def candidates(W, H, margin):
    """Candidate label slots: a fine perimeter ladder plus a coarse interior grid.

    Placement is decided by target-first scoring, never by a fixed corner order.
    Interior candidates carry a small penalty so a perimeter slot wins ties.
    """
    out = []
    steps = 10
    for i in range(steps):
        y = margin + (H - 2 * margin) / (steps - 1) * i
        y = min(y, H - margin) if i < steps - 1 else H - margin
        out.append({"name": f"L{i}", "side": "L", "x": margin, "y": y,
                    "align": "left", "kind": "perimeter", "penalty": 0.0})
        out.append({"name": f"R{i}", "side": "R", "x": W - margin, "y": y,
                    "align": "right", "kind": "perimeter", "penalty": 0.0})
    out.append({"name": "TC", "side": "C", "x": W / 2, "y": margin,
                "align": "center", "kind": "perimeter", "penalty": 0.0})
    out.append({"name": "BC", "side": "C", "x": W / 2, "y": H - margin,
                "align": "center", "kind": "perimeter", "penalty": 0.0, "vanchor": "bottom"})
    # interior candidates stay in the upper/lower bands, where scenes are usually
    # wall, sky or floor; the mid band belongs to faces, hands and actions.
    for xi, xf in enumerate([0.16, 0.24, 0.32, 0.40, 0.50, 0.60, 0.68, 0.76, 0.84]):
        for yi, yf in enumerate([0.14, 0.20, 0.26, 0.32, 0.40, 0.48, 0.56,
                                 0.64, 0.72, 0.80, 0.88]):
            out.append({"name": f"I{xi}{yi}", "side": "C", "x": W * xf, "y": H * yf,
                        "align": "center", "kind": "interior", "penalty": 0.06 * W,
                        "vanchor": "center"})
    return out



def box_at(cand, w, h, H, margin):
    if cand["align"] == "left":
        x0 = cand["x"]
    elif cand["align"] == "right":
        x0 = cand["x"] - w
    else:
        x0 = cand["x"] - w / 2
    va = cand.get("vanchor") or ("bottom" if cand["y"] >= H - margin - 1 else "top")
    if va == "bottom":
        y0 = cand["y"] - h
    elif va == "center":
        y0 = cand["y"] - h / 2
    else:
        y0 = cand["y"]
    return [x0, y0, x0 + w, y0 + h]


def edge_point(rect, ax, ay):
    cx, cy = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
    dx, dy = ax - cx, ay - cy
    if abs(dx) / max(rect[2] - rect[0], 1) > abs(dy) / max(rect[3] - rect[1], 1):
        return (rect[2] if dx > 0 else rect[0], cy)
    return (cx, rect[3] if dy > 0 else rect[1])


def overlap(a, b):
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return max(0, dx) * max(0, dy)


def contains(rect, x, y):
    return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]


# -------------------------------------------------------------- border trim
def trim_uniform_border(img, thresh=246, cap=0.24):
    """Strip near-white / near-flat bands a model adds when the reference aspect
    differs from the requested canvas (observed as letterboxing). Capped at `cap`
    of each side so a genuinely pale sky is never eaten."""
    px = img.convert("RGB").load()
    W, H = img.size

    def flat(vals):
        dark = sum(1 for v in vals if v < thresh - 8) / max(1, len(vals))
        return sum(vals) / max(1, len(vals)) > thresh and dark < 0.02

    def row_flat(y):
        step = max(1, W // 96)
        return flat([sum(px[x, y]) / 3 for x in range(0, W, step)])

    def col_flat(x):
        step = max(1, H // 96)
        return flat([sum(px[x, y]) / 3 for y in range(0, H, step)])

    top = bot = left = right = 0
    ymax, xmax = int(H * cap), int(W * cap)
    while top < ymax and row_flat(top):
        top += 1
    while bot < ymax and row_flat(H - 1 - bot):
        bot += 1
    while left < xmax and col_flat(left):
        left += 1
    while right < xmax and col_flat(W - 1 - right):
        right += 1
    if not any((top, bot, left, right)):
        return img, (0, 0, 0, 0)
    if H - top - bot < H * 0.5 or W - left - right < W * 0.5:
        return img, (0, 0, 0, 0)
    return img.crop((left, top, W - right, H - bot)), (top, bot, left, right)


# ---------------------------------------------------------------- subject mask
def inflate(box, pad_x, pad_y):
    return [box[0] - pad_x, box[1] - pad_y, box[2] + pad_x, box[3] + pad_y]


def route(rect, anchor, W, H, margin):
    """Straight when short enough, otherwise an L-elbow that hugs the nearest margin."""
    ax, ay = anchor
    ex, ey = edge_point(rect, ax, ay)
    straight = math.hypot(ax - ex, ay - ey)
    # elbow via the label's own corner (two segments, one bend)
    cands = [
        [(ex, ey), (ax, ey), (ax, ay)],
        [(ex, ey), (ex, ay), (ax, ay)],
    ]
    best = min(cands, key=lambda pts: sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
                                          for i in range(len(pts) - 1)))
    elbow = sum(math.hypot(best[i + 1][0] - best[i][0], best[i + 1][1] - best[i][1])
                for i in range(len(best) - 1))
    # margin-hugging route: along the frame corridor next to the label
    corridor_x = margin / 2 if rect[0] < W / 2 else W - margin / 2
    hug = [(ex, ey), (corridor_x, ey), (corridor_x, ay), (ax, ay)]
    hug_len = sum(math.hypot(hug[i + 1][0] - hug[i][0], hug[i + 1][1] - hug[i][1])
                  for i in range(len(hug) - 1))
    if straight <= min(elbow, hug_len):
        return [(ex, ey), (ax, ay)], straight, "straight", straight
    if elbow <= hug_len:
        return best, elbow, "elbow", straight
    return hug, hug_len, "margin", straight


# ---------------------------------------------------------------- composition
def compose_card(card, cfg, out_report):
    W = cfg["canvas"]["width"]
    margin = cfg["margin"]
    tok = cfg["tokens"]
    scale = W / cfg["reference_width"]
    ceiling = cfg["ceiling"]
    soft, hard = ceiling["soft"] * W, ceiling["hard"] * W
    cn_cfg = cfg["fonts"]

    base = Image.open(card["base"]).convert("RGB")
    if card.get("crop_bottom_px"):
        base = base.crop((0, 0, base.width, base.height - card["crop_bottom_px"]))
    border_trim = (0, 0, 0, 0)
    if card.get("trim_border", True):
        base, border_trim = trim_uniform_border(base)
    H = cfg["canvas"].get("height") or round(base.height * W / base.width)
    art = base.resize((W, H), Image.LANCZOS)
    # gentle edge restore for the resampled art only (text is drawn after, native resolution)
    if W / base.width > 1.01:
        art = art.filter(ImageFilter.UnsharpMask(radius=2.2, percent=55, threshold=3))

    # ---- protected subject boxes: a label must never sit on a person's head/face
    subject_rects = []
    for b in (card.get("subjects") or []):
        subject_rects.append(inflate([b[0] * W, b[1] * H, b[2] * W, b[3] * H],
                                     0.012 * W, 0.010 * W))

    def subject_hit(r):
        area = max(1.0, (r[2] - r[0]) * (r[3] - r[1]))
        return sum(overlap(r, s) for s in subject_rects) / area

    # ---- busyness map: a label card belongs on calm background, not on a torso
    # Edge energy is a cheap, style-independent proxy for "something is drawn
    # here". Head boxes alone cannot catch labels lying on a person's chest or
    # sleeve, which is the failure this map exists to prevent.
    BUSY_REF = float(cfg.get("busy_ref", 14.0))
    BUSY_WEIGHT = float(cfg.get("busy_weight", 0.16))
    bw, bh = 48, max(1, round(48 * H / W))
    busy_map = list(art.convert("L").filter(ImageFilter.FIND_EDGES)
                    .resize((bw, bh), Image.BOX).getdata())

    def busy_level(r):
        x0 = max(0, min(bw - 1, int(r[0] / W * bw)))
        x1 = max(x0 + 1, min(bw, int(math.ceil(r[2] / W * bw))))
        y0 = max(0, min(bh - 1, int(r[1] / H * bh)))
        y1 = max(y0 + 1, min(bh, int(math.ceil(r[3] / H * bh))))
        vals = []
        for yy in range(y0, y1):
            row = yy * bw
            vals.extend(busy_map[row + x0:row + x1])
        return sum(vals) / max(1, len(vals))

    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    max_lw = int(cfg["max_label_width_ratio"] * W)
    labels = []
    for lb in card["labels"]:
        lab = make_label(probe, lb, max_lw, scale, tok)
        finish_cn(probe, lb, lab, scale, tok, cn_cfg["chinese"], cn_cfg.get("chinese_index", 0))
        labels.append({"spec": lb, "lb": lab})

    # ---- target-first placement: a label may sit on the global grid *or* on a
    # ring around its own target, which is how a human labels a face.
    for item in labels:
        a = item["spec"].get("anchor")
        item["anchor_px"] = (a["x"] * W, a["y"] * H) if a else None
        item["needs"] = item["spec"].get("connector_policy") in ("required", "optional")

    def ring_candidates(item, W, H, margin):
        a = item["anchor_px"]
        if not a:
            return []
        ax, ay = a
        w, h = item["lb"]["w"], item["lb"]["h"]
        out = []
        dirs = ((0, -1), (0.7, -0.7), (1, 0), (0.7, 0.7),
                (0, 1), (-0.7, 0.7), (-1, 0), (-0.7, -0.7))
        for di, df in enumerate((0.04, 0.08, 0.13, 0.19, 0.26)):
            d = df * W
            for ni, (nx, ny) in enumerate(dirs):
                if nx > 0:
                    x0 = ax + nx * d
                elif nx < 0:
                    x0 = ax - w + nx * d
                else:
                    x0 = ax - w / 2
                if ny > 0:
                    y0 = ay + ny * d
                elif ny < 0:
                    y0 = ay - h + ny * d
                else:
                    y0 = ay - h / 2
                if w > W - 2 * margin or h > H - 2 * margin:
                    continue
                x0 = min(max(x0, margin), W - margin - w)
                y0 = min(max(y0, margin), H - margin - h)
                out.append({"name": f"A{di}{ni}", "x": x0, "y": y0, "align": "left",
                            "vanchor": "top", "kind": "ring", "penalty": 0.0})
        return out

    PROTECT = 0.11 * W          # no label may come closer than this to a target anchor
    grid = candidates(W, H, margin)

    def dist_point_rect(p, r):
        dx = max(r[0] - p[0], 0, p[0] - r[2])
        dy = max(r[1] - p[1], 0, p[1] - r[3])
        return math.hypot(dx, dy)

    def body_zone_cost(r):
        """Directly under a head is a neck and a torso; directly above it is hair.
        Both read as 'the card is lying on the person', so they are not free
        ground even though the head box does not cover them."""
        cost = 0.0
        rw = max(1.0, r[2] - r[0])
        for s in subject_rects:
            ov_x = max(0.0, min(r[2], s[2]) - max(r[0], s[0])) / rw
            if ov_x < 0.45:
                continue
            below = r[1] - s[3]
            above = s[1] - r[3]
            if 0 <= below < 0.16 * H:
                cost += 0.20 * W
            elif 0 <= above < 0.05 * H:
                cost += 0.12 * W
        return cost

    def own_cost(item, c, r):
        cost = c.get("penalty", 0.0)
        hit = subject_hit(r)
        if hit > 0.0:
            cost += 60.0 * W * hit       # covering a person is never acceptable
        cost += min(1.0, busy_level(r) / BUSY_REF) * BUSY_WEIGHT * W   # prefer calm ground
        cost += body_zone_cost(r) * 0.6    # a slightly longer arrow beats a card on a chest
        a = item["anchor_px"]
        if a:
            p = edge_point(r, a[0], a[1])
            cost += math.hypot(a[0] - p[0], a[1] - p[1])
            if dist_point_rect(a, r) < 0.03 * W:
                cost += 0.45 * W            # card would sit on its own target
        slot = item["spec"].get("slot")
        if slot and c.get("kind") == "perimeter":
            cost += 0 if c["name"] == slot else 0.20 * W
        return cost

    def pair_cost(r, other, other_rect):
        cost = 3.0 * overlap(r, other_rect)
        if other["anchor_px"]:
            d = dist_point_rect(other["anchor_px"], r)
            if d < PROTECT:
                cost += 0.30 * W * (1 - d / PROTECT)
        return cost

    def cross_cost(item, r, others):
        """A connector should not run across another label card or across a
        face. Sampling the straight run is enough: it is the route a reader
        follows, and the composer only draws straight or short-elbow paths."""
        a = item["anchor_px"]
        if not a:
            return 0.0
        p = edge_point(r, a[0], a[1])
        own = next((s for s in subject_rects if contains(s, a[0], a[1])), None)
        n = 18
        cost = 0.0
        for i in range(1, n):
            t = i / n
            x = p[0] + (a[0] - p[0]) * t
            y = p[1] + (a[1] - p[1]) * t
            for o in others:
                if contains(o["rect"], x, y):
                    cost += 0.55 * W / n
                    break
            for s in subject_rects:
                if s is own:
                    continue
                if contains(s, x, y):
                    cost += 0.75 * W / n
                    break
        return cost

    def choose(item, others):
        best_ok = best_any = None
        ranked = []
        for cnd in item["cands"]:
            r = box_at(cnd, item["lb"]["w"], item["lb"]["h"], H, margin)
            if not (0 <= r[0] and r[2] <= W and 0 <= r[1] and r[3] <= H):
                continue
            cost = (own_cost(item, cnd, r)
                    + sum(pair_cost(r, o, o["rect"]) for o in others)
                    + cross_cost(item, r, others))
            ranked.append((cost, cnd["name"], round(busy_level(r), 1), cnd["kind"]))
            if best_any is None or cost < best_any[0]:
                best_any = (cost, cnd, r)
            if subject_hit(r) <= 0.02 and (best_ok is None or cost < best_ok[0]):
                best_ok = (cost, cnd, r)
        if DEBUG:
            ranked.sort()
            print(f"  [{item['spec']['term']}] " + " | ".join(
                f"{n}:{c / W:.3f}W busy={b}" for c, n, b, _ in ranked[:4]))
        return best_ok or best_any

    for item in labels:
        item["cands"] = grid + ring_candidates(item, W, H, margin)
        if item["anchor_px"]:
            a = item["anchor_px"]
            item["hardness"] = min(
                math.hypot(a[0] - edge_point(box_at(c, item["lb"]["w"], item["lb"]["h"], H, margin),
                                             a[0], a[1])[0],
                           a[1] - edge_point(box_at(c, item["lb"]["w"], item["lb"]["h"], H, margin),
                                             a[0], a[1])[1])
                for c in item["cands"])
        else:
            item["hardness"] = 0

    # greedy seed, hardest label first
    order = sorted(labels, key=lambda i: (not i["needs"], -i["hardness"]))
    placed = []
    for item in order:
        cost, cnd, r = choose(item, placed)
        item["cand"], item["rect"] = cnd, r
        placed.append(item)

    # coordinate descent: re-place each label against the others until stable
    for _round in range(5):
        changed = False
        for item in labels:
            others = [o for o in labels if o is not item]
            cur = own_cost(item, item["cand"], item["rect"]) + \
                sum(pair_cost(item["rect"], o, o["rect"]) for o in others) + \
                cross_cost(item, item["rect"], others)
            cost, cnd, r = choose(item, others)
            better = cost < cur - 1
            repair = subject_hit(item["rect"]) > 0.02 and subject_hit(r) <= 0.02
            if better or repair:
                item["cand"], item["rect"] = cnd, r
                changed = True
        if not changed:
            break

    if DEBUG:
        for it in placed:
            r = it["rect"]
            print(f"    FINAL {it['spec']['term']}: rect={[round(v) for v in r]} "
                  f"hit={subject_hit(r):.3f} body={body_zone_cost(r)/W:.3f}W "
                  f"busy={busy_level(r):.1f} cand={it['cand']['name']}")

    # ---- connector routing with ceiling enforcement
    warnings = []
    for item in placed:
        if not item["needs"] or not item["anchor_px"]:
            item["connector"] = None
            continue
        pts, length, kind, straight = route(item["rect"], item["anchor_px"], W, H, margin)
        if straight > hard:
            # one repair attempt: relocate to the candidate closest to the anchor
            used = {p["cand"]["name"] for p in placed}
            options = []
            for c in item["cands"]:
                if c["name"] in used:
                    continue
                r = box_at(c, item["lb"]["w"], item["lb"]["h"], H, margin)
                if not (0 <= r[0] and r[2] <= W and 0 <= r[1] and r[3] <= H):
                    continue
                clash = sum(overlap(r, p["rect"]) for p in placed if p is not item)
                if clash or subject_hit(r) > 0.02:
                    continue
                ep = edge_point(r, item["anchor_px"][0], item["anchor_px"][1])
                d = math.hypot(item["anchor_px"][0] - ep[0], item["anchor_px"][1] - ep[1])
                options.append((d, c, r))
            if options:
                options.sort(key=lambda o: o[0])
                d, c, r = options[0]
                item["cand"], item["rect"] = c, r
                pts, length, kind, straight = route(item["rect"], item["anchor_px"], W, H, margin)
                item.setdefault("repairs", []).append(f"relocated to {c['name']}")
        if length > hard:
            # is a protected subject blocking every nearer candidate? then the
            # ceiling is geometrically impossible, not an algorithm miss
            nearest = None
            for c in item["cands"]:
                r = box_at(c, item["lb"]["w"], item["lb"]["h"], H, margin)
                if not (0 <= r[0] and r[2] <= W and 0 <= r[1] and r[3] <= H):
                    continue
                if subject_hit(r) > 0.02:
                    continue
                if any(overlap(r, p["rect"]) for p in placed if p is not item):
                    continue
                ep = edge_point(r, item["anchor_px"][0], item["anchor_px"][1])
                d = math.hypot(item["anchor_px"][0] - ep[0], item["anchor_px"][1] - ep[1])
                nearest = d if nearest is None else min(nearest, d)
            if nearest is None or nearest > hard:
                item["geometry_limited"] = True
                warnings.append(
                    f"{item['spec']['term']}: {length / W:.0%} of width — no free area within "
                    f"{hard / W:.0%} of the target (recompose the scene)")
        if length > hard and item["spec"].get("connector_policy") == "optional":
            item["connector"] = None
            warnings.append(f"{item['spec']['term']}: connector dropped (would be {length / W:.0%} of width)")
            continue
        if length > soft:
            warnings.append(f"{item['spec']['term']}: connector {length / W:.0%} of width ({kind})")
        item["connector"] = {"points": pts, "length": length, "reach": straight, "kind": kind}

    for item in placed:
        if subject_hit(item["rect"]) > 0.02:
            warnings.append(f"{item['spec']['term']}: label covers a person "
                            f"({subject_hit(item['rect']):.0%} of the card)")

    # ---- draw
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for item in placed:
        c = item["connector"]
        if not c:
            continue
        od.line(c["points"], fill=tok["connector"] + (int(0.78 * 255),), width=max(2, round(2.5 * scale)), joint="curve")
        ax, ay = item["anchor_px"]
        r = max(4, round(6 * scale))
        od.ellipse([ax - r, ay - r, ax + r, ay + r], fill=tok["dot"] + (235,), outline=(255, 255, 255, 245), width=2)

    radius = max(10, round(tok["radius_ratio"] * W))
    for item in placed:
        rect, lb = item["rect"], item["lb"]
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle(
            [rect[0] + 3, rect[1] + 7, rect[2] + 3, rect[3] + 9],
            radius=radius, fill=(31, 41, 55, 34))
        overlay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
        od.rounded_rectangle(rect, radius=radius, fill=tok["card_fill"] + (250,),
                             outline=(14, 43, 109, 16), width=max(1, round(1.5 * scale)))
        align = "left" if rect[0] < W / 2 - 1 and rect[2] < W * 0.75 else ("right" if rect[2] > W * 0.75 else "center")
        y = rect[1] + lb["pad_y"]

        def draw_line(text, font, color, lh):
            nonlocal y
            tw = text_w(od, text, font)
            if align == "left":
                x = rect[0] + lb["pad_x"]
            elif align == "right":
                x = rect[2] - lb["pad_x"] - tw
            else:
                x = rect[0] + (rect[2] - rect[0] - tw) / 2
            od.text((x, y), text, font=font, fill=color + (255,))
            y += lh

        for line in lb["en"]:
            draw_line(line, lb["f_en"], tok["en_color"], lb["en_lh"])
        y += 8
        for line in lb["ip"]:
            draw_line(line, lb["f_ip"], tok["ipa_color"], lb["ip_lh"])
        y += 4
        for line in lb["cn"]:
            draw_line(line, lb["f_cn"], tok["cn_color"], lb["cn_lh"])

    final = art.convert("RGBA")
    final.alpha_composite(overlay)
    out = final.convert("RGB")
    os.makedirs(os.path.dirname(card["out"]) or ".", exist_ok=True)
    out.save(card["out"], "PNG", optimize=True)
    if card.get("jpg"):
        out.save(card["jpg"], "JPEG", quality=90, optimize=True, progressive=True)
    if card.get("debug_protect"):
        dbg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dbg)
        for s in subject_rects:
            dd.rectangle(s, outline=(214, 42, 42, 255), width=max(2, round(4 * scale)))
        for i in placed:
            dd.rectangle(i["rect"], outline=(32, 96, 214, 255), width=max(2, round(3 * scale)))
        dbg_path = os.path.splitext(card["out"])[0] + "_protect.png"
        Image.alpha_composite(art.convert("RGBA"), dbg).convert("RGB").save(dbg_path)
        print("  protect overlay:", dbg_path)

    report = {
        "card_id": card["card_id"],
        "canvas": [W, H],
        "ceiling_px": {"soft": round(soft), "hard": round(hard)},
        "subjects": [[round(v) for v in s] for s in subject_rects],
        "border_trim": list(border_trim),
        "labels": [{
            "term": i["spec"]["term"],
            "slot": i["cand"]["name"],
            "rect": [round(v) for v in i["rect"]],
            "subject_overlap": round(subject_hit(i["rect"]), 3),
            "connector_policy": i["spec"].get("connector_policy"),
            "connector_kind": (i["connector"] or {}).get("kind"),
            "connector_px": round((i["connector"] or {}).get("length", 0)),
            "connector_norm": round((i["connector"] or {}).get("reach", 0) / W, 3),
            "busy": round(busy_level(i["rect"]), 1),
            "body_zone": round(body_zone_cost(i["rect"]) / W, 3),
            "repairs": i.get("repairs", []),
            "geometry_limited": bool(i.get("geometry_limited")),
        } for i in placed],
        "warnings": warnings,
        "hard_fail": [i["spec"]["term"] for i in placed
                      if i["spec"].get("connector_policy") == "required"
                      and (i["connector"] or {}).get("length", 0) > hard
                      and not i.get("geometry_limited")],
        "geometry_limited": [i["spec"]["term"] for i in placed if i.get("geometry_limited")],
    }
    out_report.append(report)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    cfg = json.load(open(args.config, encoding="utf-8"))
    merged = json.loads(json.dumps(DEFAULTS))
    for k, v in cfg.items():
        if isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
            merged[k].update(v)
        else:
            merged[k] = v
    cfg = merged
    for key in ("card_fill", "en_color", "ipa_color", "cn_color", "connector", "dot"):
        if key in cfg["tokens"] and isinstance(cfg["tokens"][key], list):
            cfg["tokens"][key] = tuple(cfg["tokens"][key])
    if "margin" not in cfg:
        cfg["margin"] = round(cfg["margin_ratio"] * cfg["canvas"]["width"])

    reports = []
    fit_ratios = [None] + list(cfg.get("fit_width_retries") or [0.28, 0.24])
    for card in cfg["cards"]:
        if args.only and card["card_id"] not in args.only:
            continue
        stem, ext = os.path.splitext(card["out"])
        variants = []
        for fr in fit_ratios:
            sub = json.loads(json.dumps(cfg))
            sub.pop("cards", None)
            card2 = json.loads(json.dumps(card))
            ratio = fr if fr else sub["max_label_width_ratio"]
            sub["max_label_width_ratio"] = ratio
            for k in ("card_fill", "en_color", "ipa_color", "cn_color", "connector", "dot"):
                if isinstance(sub["tokens"].get(k), list):
                    sub["tokens"][k] = tuple(sub["tokens"][k])
            card2["out"] = f"{stem}__w{int(ratio * 100)}{ext}"
            card2["jpg"] = None
            card2.pop("debug_protect", None)
            tmp = []
            r = compose_card(card2, sub, tmp)
            hits = sum(1 for lb in r["labels"] if lb.get("subject_overlap", 0) > 0.02)
            # a shorter connector is not better if it is short because the card
            # is lying on the person: body-zone hits outrank length
            body = sum(1 for lb in r["labels"] if lb.get("body_zone", 0) > 0)
            mx = max([lb["connector_norm"] for lb in r["labels"]] or [0])
            fails = len(r["hard_fail"])
            geom = len(r["geometry_limited"])
            variants.append(((hits, geom, body, fails, round(mx, 3)), ratio, card2["out"], r))

        best_score, best_ratio, best_out, best_r = min(variants, key=lambda v: v[0])
        for _, _, out, _r in variants:
            if out != best_out and os.path.exists(out):
                os.remove(out)
        if os.path.exists(best_out) and best_out != card["out"]:
            os.replace(best_out, card["out"])
        best_r["label_width_ratio"] = round(best_ratio, 2)
        best_r["width_variants"] = [vars_[1] for vars_ in variants]
        if card.get("jpg"):
            from PIL import Image as _I
            _I.open(card["out"]).convert("RGB").save(card["jpg"], "JPEG", quality=90,
                                                     optimize=True, progressive=True)
        if card.get("debug_protect"):
            dbgdir = os.path.dirname(card["out"])
            _I2 = __import__("PIL.Image", fromlist=["Image"])
            im = _I2.open(card["out"]).convert("RGB")
            d = ImageDraw.Draw(im)
            Wd, Hd = im.size
            for b in (card.get("subjects") or []):
                d.rectangle([b[0] * Wd, b[1] * Hd, b[2] * Wd, b[3] * Hd],
                            outline=(214, 42, 42), width=4)
            for lb in best_r["labels"]:
                d.rectangle(lb["rect"], outline=(32, 96, 214), width=3)
            im.save(os.path.splitext(card["out"])[0] + "_protect.png")
        reports.append(best_r)
        print(f"{best_r['card_id']:14s} labels={len(best_r['labels'])} "
              f"max={best_score[2]:.2f}W fails={best_score[1]} hits={best_score[0]} "
              f"width={best_ratio:.2f} warn={len(best_r['warnings'])}")

    path = args.report or os.path.join(os.path.dirname(args.config), "compose_report.json")
    json.dump(reports, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("report:", path)


if __name__ == "__main__":
    sys.exit(main())
