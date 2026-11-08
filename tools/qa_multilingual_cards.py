#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Source, mapping, layout and style-reference QA for multilingual previews."""
import argparse
import hashlib
import json
import sys
import unicodedata
from pathlib import Path

from PIL import Image

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
POLICY = {
    "direct_anchor": "required",
    "action_anchor": "optional",
    "relation_anchor": "optional",
    "scene_state": "none",
    "dialogue_phrase": "none",
    "timeline_segment": "none",
    "comparison_zone": "none",
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def resolve(path, base):
    p = Path(path)
    return p if p.is_absolute() else (base / p).resolve()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--report", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    config_path = Path(args.config).resolve()
    config_dir = config_path.parent
    cfg = load_json(config_path)
    report_path = resolve(args.report or cfg.get("report", "multilingual_compose_report.json"), config_dir)
    report_rows = load_json(report_path)
    reports = {r["card_id"]: r for r in report_rows}
    failures = []

    profile_path = resolve(cfg.get("language_profile", ""), PACKAGE_ROOT)
    if not profile_path.is_file():
        failures.append("LANGUAGE_PROFILE_UNKNOWN")
        profile = {}
    else:
        profile = load_json(profile_path)
    if profile and profile.get("locale") != cfg.get("target_language"):
        failures.append("LANGUAGE_PROFILE_UNKNOWN: locale does not match run configuration")

    ref = cfg.get("style_reference")
    ref_path = PACKAGE_ROOT / ref if ref else None
    actual_ref_hash = sha256_file(ref_path) if ref_path and ref_path.is_file() else None
    expected_ref_hash = cfg.get("style_reference_sha256")
    if not actual_ref_hash:
        failures.append("STYLE_REFERENCE_UNAVAILABLE")
    elif actual_ref_hash != expected_ref_hash:
        failures.append("STYLE_REFERENCE_MISMATCH")

    master_path = resolve(cfg.get("vocabulary_master", ""), config_dir)
    if not master_path.is_file():
        failures.append("SOURCE_DATA_AMBIGUOUS: vocabulary_master is missing")
        master = []
    else:
        master = load_json(master_path)
    source_by_id = {x["id"]: x for x in master}
    assigned = {}
    card_results = []

    for card in cfg.get("cards", []):
        cid = card["card_id"]
        card_failures = []
        rep = reports.get(cid)
        if not rep:
            card_failures.append("COMPOSER_UNAVAILABLE: compose report missing")
            rep = {"labels": [], "hard_fail": ["compose report missing"], "geometry_limited": []}
        request = card.get("stage07_request", {})
        attached_paths = request.get("referenced_image_paths", [])
        if not card.get("style_reference_attached") or str(ref_path) not in attached_paths:
            card_failures.append("STYLE_REFERENCE_NOT_ATTACHED: actual Stage 07 request record lacks the image path")
        if card.get("style_reference") != ref or card.get("style_reference_sha256") != actual_ref_hash:
            card_failures.append("STYLE_REFERENCE_MISMATCH: per-card reference differs from the packaged asset")

        for label in card.get("labels", []):
            source_id = label.get("source_id")
            source = source_by_id.get(source_id)
            assigned[source_id] = assigned.get(source_id, 0) + 1
            if not source:
                card_failures.append(f"COVERAGE_ERROR: {source_id} is not in the source ledger")
                continue
            source_form = source.get("display_form") or source["term"]
            display_form = label.get("display_form") or label.get("target_term") or label.get("term")
            if display_form != source_form:
                card_failures.append(f"TEXT_ERROR: target form differs from source for {source_id}")
            source_gloss = source.get("gloss") or {"text": source.get("chinese"), "language": "zh-CN"}
            label_gloss = label.get("gloss") or {"text": label.get("chinese"), "language": label.get("gloss_language", "zh-CN")}
            if label_gloss.get("text") != source_gloss.get("text") or label_gloss.get("language") != source_gloss.get("language"):
                card_failures.append(f"TEXT_ERROR: gloss or gloss language differs from source for {source_id}")
            source_reading = source.get("reading") or (source.get("pronunciation") or {}).get("value")
            label_reading = label.get("reading") or (label.get("pronunciation") or {}).get("value")
            if label_reading != source_reading:
                card_failures.append(f"TEXT_ERROR: reading differs from source for {source_id}")
            if unicodedata.normalize("NFC", display_form or "") != unicodedata.normalize("NFC", source_form or ""):
                card_failures.append(f"TEXT_ERROR: rendered normalized form differs from source for {source_id}")
            mode = label.get("mapping_mode")
            expected_policy = POLICY.get(mode)
            actual_policy = label.get("connector_policy", expected_policy)
            if not expected_policy or actual_policy != expected_policy:
                card_failures.append(f"LINE_MAPPING_ERROR: connector policy mismatch for {source_id}")
            if actual_policy in {"required", "optional"} and not label.get("anchor"):
                card_failures.append(f"LINE_MAPPING_ERROR: anchor missing for {source_id}")

        expected_ids = {x.get("source_id") for x in card.get("labels", [])}
        reported = {x.get("term") for x in rep.get("labels", [])}
        expected_terms = {x.get("term") for x in card.get("labels", [])}
        if len(expected_ids) != len(card.get("labels", [])):
            card_failures.append("COVERAGE_ERROR: duplicate source id on the card")
        if not expected_terms.issubset(reported):
            card_failures.append("COMPOSER_UNAVAILABLE: one or more labels are missing from the compose report")
        if rep.get("hard_fail"):
            card_failures.append("STYLE_FAIL_CONNECTOR_V3: required connector exceeded the hard ceiling")
        if rep.get("geometry_limited"):
            card_failures.append("STYLE_FAIL_CONNECTOR_V3: geometry limited; scene needs review")
        for item in rep.get("labels", []):
            if item.get("subject_overlap", 0) > 0.02:
                card_failures.append(f"LAYOUT_COLLISION: label overlaps a declared subject: {item.get('term')}")
            if item.get("protected_overlap", 0) > 0.02:
                card_failures.append(f"LAYOUT_COLLISION: label overlaps a protected learning target: {item.get('term')}")
        rects = [x.get("rect", []) for x in rep.get("labels", [])]
        for i, a in enumerate(rects):
            for b in rects[i + 1:]:
                if len(a) == 4 and len(b) == 4 and a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                    card_failures.append("LAYOUT_COLLISION: label rectangles overlap")

        base = resolve(card["base"], config_dir)
        out = resolve(card["out"], config_dir)
        if not base.is_file() or not out.is_file():
            card_failures.append("COMPOSER_UNAVAILABLE: base or composed image is missing")
        elif len(rep.get("canvas", [])) == 2:
            im = Image.open(out)
            if list(im.size) != rep["canvas"]:
                card_failures.append("LAYOUT_COLLISION: output dimensions differ from the compose report")

        card_results.append({
            "card_id": cid,
            "status": "FAIL" if card_failures else "PASS",
            "failure_codes": sorted(set(x.split(":", 1)[0] for x in card_failures)),
            "notes": card_failures,
            "source_ids": [x.get("source_id") for x in card.get("labels", [])],
            "image": str(out),
        })
        failures.extend(f"{cid}: {failure}" for failure in card_failures)

    expected_source_ids = {x["id"] for x in master}
    if set(assigned) != expected_source_ids or any(assigned.get(key, 0) != 1 for key in expected_source_ids):
        failures.append("COVERAGE_ERROR: every source entry must appear exactly once")

    profile_status = profile.get("status")
    if profile_status not in {"preview", "validated"}:
        failures.append("LANGUAGE_PROFILE_UNVALIDATED: profile status must be preview or validated")
    overall = "FAIL" if failures else ("APPROVED" if profile_status == "validated" else "PREVIEW_PASS")
    result = {
        "batch_id": cfg.get("batch_id"),
        "overall": overall,
        "target_language": cfg.get("target_language"),
        "language_profile": str(profile_path),
        "language_profile_status": profile_status,
        "style_reference": ref,
        "style_reference_sha256": actual_ref_hash,
        "style_reference_attached": all(c.get("style_reference_attached") is True for c in cfg.get("cards", [])),
        "source_coverage": {key: assigned.get(key, 0) for key in sorted(expected_source_ids)},
        "cards": card_results,
        "failure_codes": sorted(set(x.split(":", 1)[0] for x in failures)),
        "notes": failures,
    }
    output = resolve(args.out or cfg.get("qa_report", "multilingual_qa_report.json"), config_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MULTILINGUAL QA: {overall}")
    print("Report:", output)
    for issue in failures:
        print(" -", issue)
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
