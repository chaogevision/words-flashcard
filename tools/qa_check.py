#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 09 QA gate for deterministic-compose runs.

Consumes the run config + the composer report + the authoritative vocabulary
master, and writes one QAReport per card plus a batch summary.

Usage
-----
    python3 tools/qa_check.py run_config.json --report compose_report.json \
        --vocabulary vocabulary_master.json --out qa/

Hard failures block `APPROVED` exactly as `core/qa_rules.md` requires; the
connector ceiling comes from the active platform Adapter.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image

POLICY_FOR_MODE = {
    "direct_anchor": "required",
    "action_anchor": "optional",
    "relation_anchor": "optional",
    "scene_state": "none",
    "dialogue_phrase": "none",
    "timeline_segment": "none",
    "comparison_zone": "none",
}

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
STYLE_REFERENCE_PATHS = {
    "assets/grade_style_references/primary_art.png",
    "assets/grade_style_references/middle_art.png",
    "assets/grade_style_references/high_art.png",
}


def resolve_style_reference(ref, config_dir):
    if ref not in STYLE_REFERENCE_PATHS:
        return None
    candidates = [PACKAGE_ROOT / ref, Path(config_dir) / ref]
    return next((p for p in candidates if p.is_file()), None)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--report", default=None)
    ap.add_argument("--vocabulary", default=None)
    ap.add_argument("--out", default="qa")
    ap.add_argument("--min-base-width", type=int, default=1536)
    ap.add_argument("--max-upscale", type=float, default=1.4)
    ap.add_argument("--adapter", default="adapters/workbuddy/ADAPTER.md")
    ap.add_argument("--platform", default="workbuddy")
    args = ap.parse_args()

    cfg = json.load(open(args.config, encoding="utf-8"))
    rep_path = args.report or os.path.join(os.path.dirname(args.config), "compose_report.json")
    reports = {r["card_id"]: r for r in json.load(open(rep_path, encoding="utf-8"))}
    master = {}
    if args.vocabulary and os.path.exists(args.vocabulary):
        for m in json.load(open(args.vocabulary, encoding="utf-8")):
            master.setdefault(m["term"], m)

    # The style reference must be one of the art-only assets and its packaged
    # bytes must match the recorded digest. Every card must separately attest
    # that the actual Stage 07 request included this image input.
    ref = cfg.get("style_reference")
    expected_ref_sha = cfg.get("style_reference_sha256")
    config_dir = os.path.dirname(os.path.abspath(args.config))
    ref_path = resolve_style_reference(ref, config_dir)
    actual_ref_sha = sha256_file(ref_path) if ref_path else None
    hash_matches = bool(expected_ref_sha and actual_ref_sha == expected_ref_sha)
    reference_issues = []
    if ref not in STYLE_REFERENCE_PATHS:
        reference_issues.append("STYLE_REFERENCE_MISMATCH: reference must be the matching *_art.png asset")
    if not ref_path:
        reference_issues.append("STYLE_REFERENCE_UNAVAILABLE: packaged style reference file is missing")
    if not expected_ref_sha or not hash_matches:
        reference_issues.append("STYLE_REFERENCE_HASH_MISMATCH: recorded SHA-256 does not match the packaged image")
    style_gate = {
        "style_reference": ref,
        "style_reference_sha256": expected_ref_sha,
        "actual_sha256": actual_ref_sha,
        "present": bool(ref_path),
        "hash_matches": hash_matches,
        "status": "FAIL" if reference_issues else "PASS",
    }

    W = cfg["canvas"]["width"]
    ceiling = cfg.get("ceiling", {"soft": 0.15, "hard": 0.26})
    os.makedirs(args.out, exist_ok=True)

    assigned, results, batch_fail = {}, [], False
    for card in cfg["cards"]:
        cid = card["card_id"]
        rep = reports[cid]
        data, mapping, layout, style, style_ref_issues = [], [], [], [], list(reference_issues)

        if card.get("style_reference") != ref:
            style_ref_issues.append("STYLE_REFERENCE_MISMATCH: card reference differs from the batch reference")
        if card.get("style_reference_sha256") != actual_ref_sha:
            style_ref_issues.append("STYLE_REFERENCE_HASH_MISMATCH: card digest differs from the packaged image")
        if card.get("style_reference_attached") is not True:
            style_ref_issues.append("STYLE_REFERENCE_NOT_ATTACHED: actual Stage 07 request did not record the reference image")
        if args.platform == "workbuddy" and cfg.get("input_fidelity") != "high":
            style_ref_issues.append("STYLE_REFERENCE_FIDELITY: WorkBuddy requires input_fidelity=high")
        style.extend(style_ref_issues)

        for lb in card["labels"]:
            term = lb["term"]
            assigned[term] = assigned.get(term, 0) + 1
            src = master.get(term)
            if master and not src:
                data.append(f"{term}: not present in curriculum source")
            if src:
                if lb.get("english") != src["term"]:
                    data.append(f"{term}: English differs from source")
                if (lb.get("ipa") or None) != (src.get("ipa") or None):
                    data.append(f"{term}: IPA differs from source")
                if lb.get("chinese") != src["chinese"]:
                    data.append(f"{term}: gloss differs from source")
            expect = POLICY_FOR_MODE.get(lb.get("mapping_mode"), "none")
            pol = lb.get("connector_policy", expect)
            if pol != expect:
                mapping.append(f"{term}: connector policy {pol} != mode default {expect}")
            if pol in ("required", "optional") and not lb.get("anchor"):
                mapping.append(f"{term}: connector without anchor")

        # geometry checks from the composer report
        lreps = rep["labels"]
        rects = [(l["term"], l["rect"]) for l in lreps]
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                a, b = rects[i][1], rects[j][1]
                if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                    layout.append(f"label collision {rects[i][0]} / {rects[j][0]}")
        for l in lreps:
            w = l["rect"][2] - l["rect"][0]
            if w > 0.4 * W:
                layout.append(f"{l['term']}: label wider than 40% of canvas")
            if l["connector_norm"] > ceiling["hard"]:
                (mapping if l["connector_policy"] == "required" else style).append(
                    f"{l['term']}: connector {l['connector_norm']:.0%} of width exceeds hard ceiling")
        if rep.get("hard_fail"):
            mapping.append(f"connector ceiling violated: {rep['hard_fail']}")
        if rep.get("geometry_limited"):
            style.append(f"geometry-limited (scene has no free area near the target): "
                         f"{rep['geometry_limited']}")

        # subject protection: no label may cover a person, and the boxes must be declared
        subjects = rep.get("subjects") or []
        for l in lreps:
            if l.get("subject_overlap", 0) > 0.02:
                layout.append(f"{l['term']}: label covers a subject "
                              f"({l['subject_overlap']:.0%} of the card area)")
        if not subjects and card.get("subjects_required", True) and \
                any(lb.get("anchor") for lb in card["labels"]):
            style.append("no `subjects` boxes declared — subject protection unverifiable "
                         "(declare them, or set subjects_required=false for a scene without people)")

        # asset checks
        base = Image.open(card["base"])
        if base.width < args.min_base_width:
            style.append(f"base illustration {base.width}px < required {args.min_base_width}px")
        ratio = W / base.width
        if ratio > args.max_upscale:
            style.append(f"upscale {ratio:.2f}x exceeds {args.max_upscale}x (soft output)")
        card_img = Image.open(card["out"])
        if abs(card_img.width / card_img.height - W / rep["canvas"][1]) > 0.01:
            layout.append("output aspect differs from canvas spec")

        hard = bool(data or mapping or layout or style)
        batch_fail = batch_fail or hard
        failure_codes = []
        if data:
            failure_codes.append("TEXT_ERROR")
        if mapping:
            failure_codes.append("LINE_MAPPING_ERROR")
        if layout:
            failure_codes.append("LAYOUT_COLLISION")
        if style_ref_issues:
            failure_codes.extend(sorted({issue.split(":", 1)[0] for issue in style_ref_issues}))
        elif style:
            failure_codes.append("STYLE_DRIFT")
        qa = {
            "card_id": cid,
            "overall": "FAIL" if hard else "PASS",
            "checks": {
                "data_qa": "FAIL" if data else "PASS",
                "mapping_qa": "FAIL" if mapping else "PASS",
                "layout_qa": "FAIL" if layout else "PASS",
                "style_qa": "FAIL" if style else "PASS",
                "style_reference": "FAIL" if style_ref_issues else "PASS",
            },
            "failure_codes": sorted(set(failure_codes)),
            "notes": data + mapping + layout + style,
            "platform": args.platform,
            "adapter": args.adapter,
            "connector_token": "connector.v3.light",
            "style_reference": {
                "path": card.get("style_reference"),
                "sha256": card.get("style_reference_sha256"),
                "attached": card.get("style_reference_attached") is True,
            },
            "connector_max_norm": max([l["connector_norm"] for l in lreps] or [0]),
            "warnings": rep.get("warnings", []),
            "result": "QA_FAILED" if hard else "APPROVED",
        }
        json.dump(qa, open(os.path.join(args.out, f"{cid.lower()}.qa.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        results.append(qa)

    missing = [t for t in master if t not in assigned]
    dup = [t for t, n in assigned.items() if n > 1]
    if master and (missing or dup):
        batch_fail = True

    if any(r["checks"]["style_reference"] == "FAIL" for r in results):
        style_gate["status"] = "FAIL"
    style_gate["attached_cards"] = sum(1 for r in results if r["style_reference"]["attached"])
    style_gate["cards"] = len(results)

    summary = {
        "cards": len(results),
        "approved": sum(1 for r in results if r["result"] == "APPROVED"),
        "coverage": {"assigned": len(assigned), "missing": missing, "duplicated": dup},
        "connector_max_norm": max([r["connector_max_norm"] for r in results] or [0]),
        "ceiling": ceiling,
        "style_reference": style_gate,
        "result": "FAIL" if batch_fail or style_gate["status"] != "PASS" else "PASS",
    }
    json.dump(summary, open(os.path.join(args.out, "batch_summary.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
