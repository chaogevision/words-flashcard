#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministically compose target-language labels over text-free scene art.

The legacy compose_cards.py contract remains available for English runs. This
entry point accepts generic target_term / reading / gloss fields and delegates
geometry to the same target-first composer.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

from PIL import ImageFont, features

PACKAGE_ROOT = Path(__file__).resolve().parents[1]

FONT_CANDIDATES = {
    "latin_bold": [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    ],
    "latin_regular": [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ],
    "japanese": [
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
    ],
    "korean": [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ],
    "gloss_cjk": [
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
    ],
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def choose_font(role, override=None):
    candidates = [override] if override else FONT_CANDIDATES[role]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            try:
                ImageFont.truetype(candidate, 32)
                return candidate
            except OSError:
                continue
    raise RuntimeError(f"TEXT_SHAPING_UNAVAILABLE: no usable {role} font was found")


def verify_glyphs(path, text, role):
    font = ImageFont.truetype(path, 48)
    missing = font.getmask(chr(0x10FFFF))
    # Pillow's ImagingCore supports the buffer protocol across supported
    # versions; it does not consistently expose a ``tobytes`` method.
    missing_bytes = bytes(missing)
    missing_size = missing.size
    absent = []
    for char in set(text):
        if char.isspace() or unicodedata.combining(char) or unicodedata.category(char) in {"Cf", "Mn", "Me"}:
            continue
        mask = font.getmask(char)
        if mask.size == missing_size and bytes(mask) == missing_bytes:
            absent.append(f"U+{ord(char):04X}")
    if absent:
        raise RuntimeError(f"FONT_GLYPH_MISSING: {role} font {path} lacks {', '.join(sorted(absent))}")


def script_role(language, gloss_language=None):
    if gloss_language and gloss_language.split("-")[0] in {"zh", "ja"}:
        return "gloss_cjk"
    if language == "ja":
        return "japanese"
    if language == "ko":
        return "korean"
    return "latin_regular"


def load_profile(config, config_dir):
    profile_path = config.get("language_profile")
    if not profile_path:
        raise RuntimeError("LANGUAGE_PROFILE_UNKNOWN: set language_profile for a multilingual batch")
    candidate = Path(profile_path)
    if not candidate.is_absolute():
        candidate = PACKAGE_ROOT / candidate
        if not candidate.is_file():
            candidate = config_dir / profile_path
    if not candidate.is_file():
        raise RuntimeError(f"LANGUAGE_PROFILE_UNKNOWN: profile not found: {profile_path}")
    profile = json.loads(candidate.read_text(encoding="utf-8"))
    if config.get("target_language") not in (None, profile["locale"]):
        raise RuntimeError("LANGUAGE_PROFILE_UNKNOWN: target_language does not match the profile locale")
    ws = profile["writing_system"]
    if ws["direction"] != "ltr" or ws["shaping"] in {"complex", "bidi"}:
        if not features.check("raqm"):
            raise RuntimeError("TEXT_SHAPING_UNAVAILABLE: active Pillow build has no RAQM shaping")
    return candidate, profile


def target_form(label):
    return label.get("display_form") or label.get("target_term") or label.get("term")


def pronunciation_text(label):
    if label.get("reading"):
        return label["reading"]
    if label.get("ipa"):
        return label["ipa"]
    value = label.get("pronunciation")
    if isinstance(value, dict):
        return value.get("value") or ""
    return value or ""


def gloss_fields(label):
    value = label.get("gloss")
    if isinstance(value, dict):
        return value.get("text", ""), value.get("language", "zh-CN")
    return label.get("chinese", ""), label.get("gloss_language", "zh-CN")


def compose(config_path):
    config_path = Path(config_path).resolve()
    config_dir = config_path.parent
    config = json.loads(config_path.read_text(encoding="utf-8"))
    profile_path, profile = load_profile(config, config_dir)
    if profile["normalization"] != "NFC":
        raise RuntimeError("LANGUAGE_PROFILE_UNKNOWN: MVP renderer requires NFC display normalization")

    ref = config.get("style_reference")
    ref_path = PACKAGE_ROOT / ref if ref else None
    if not ref_path or not ref_path.is_file():
        raise RuntimeError("STYLE_REFERENCE_UNAVAILABLE: packaged art-only style reference is missing")
    actual_sha = sha256_file(ref_path)
    expected_sha = config.get("style_reference_sha256")
    if actual_sha != expected_sha:
        raise RuntimeError("STYLE_REFERENCE_MISMATCH: style reference hash does not match the package")

    user_fonts = config.get("fonts", {})
    language = profile["language"]
    target_role = script_role(language)
    if language not in {"ja", "ko"}:
        target_role = "latin_bold"
    gloss_languages = {gloss_fields(label)[1] for card in config["cards"] for label in card["labels"]}
    if len(gloss_languages) != 1:
        raise RuntimeError("SOURCE_DATA_AMBIGUOUS: one batch must use one gloss language")
    gloss_language = next(iter(gloss_languages))
    fonts = {
        "target": choose_font(target_role, user_fonts.get("target")),
        "pronunciation": choose_font(target_role if language == "ja" else "latin_regular", user_fonts.get("pronunciation")),
        "gloss": choose_font(script_role("", gloss_language), user_fonts.get("gloss")),
        "english": choose_font("latin_bold", user_fonts.get("target")) if language not in {"ja", "ko"} else choose_font(target_role, user_fonts.get("target")),
        "ipa": choose_font(target_role if language == "ja" else "latin_regular", user_fonts.get("pronunciation")),
        "chinese": choose_font(script_role("", gloss_language), user_fonts.get("gloss")),
        "chinese_index": 0,
        "gloss_index": 0,
    }

    normalized = {
        "canvas": config.get("canvas", {"width": 1536, "height": 0}),
        "margin": config.get("margin", 72),
        "max_label_width_ratio": config.get("max_label_width_ratio", 0.34),
        "fit_width_retries": config.get("fit_width_retries", [0.28, 0.24]),
        "reference_width": config.get("reference_width", 1536),
        "ceiling": config.get("ceiling", {"soft": 0.15, "hard": 0.26}),
        "fonts": fonts,
        "style_reference": ref,
        "style_reference_sha256": expected_sha,
        "input_fidelity": config.get("input_fidelity"),
        "cards": [],
    }
    for card in config["cards"]:
        if card.get("style_reference_attached") is not True:
            raise RuntimeError("STYLE_REFERENCE_NOT_ATTACHED: card must record actual Stage 07 attachment")
        base = Path(card["base"])
        out = Path(card["out"])
        if not base.is_absolute():
            base = config_dir / base
        if not out.is_absolute():
            out = config_dir / out
        normalized_card = dict(card)
        normalized_card.update({"base": str(base), "out": str(out)})
        normalized_labels = []
        for label in card["labels"]:
            form = target_form(label)
            gloss, gloss_language = gloss_fields(label)
            if not form or not gloss:
                raise RuntimeError(f"SOURCE_DATA_AMBIGUOUS: missing target form or gloss for {label.get('term')}")
            item = dict(label)
            item["term"] = label.get("term") or label.get("source_id") or form
            item["english"] = unicodedata.normalize("NFC", form)
            item["ipa"] = unicodedata.normalize("NFC", pronunciation_text(label))
            item["chinese"] = unicodedata.normalize("NFC", gloss)
            item["wrap_mode"] = profile["term_wrap"]
            item["gloss_wrap_mode"] = "graphemes" if gloss_language.split("-")[0] in {"zh", "ja", "ko"} else "latin_words"
            verify_glyphs(fonts["target"], item["english"], "target term")
            if item["ipa"]:
                verify_glyphs(fonts["pronunciation"], item["ipa"], "pronunciation")
            verify_glyphs(fonts["gloss"], item["chinese"], "gloss")
            normalized_labels.append(item)
        normalized_card["labels"] = normalized_labels
        normalized["cards"].append(normalized_card)

    normalized["fit_width_retries"] = config.get("fit_width_retries", [0.28, 0.24])
    with tempfile.TemporaryDirectory(prefix="flashcard-multilingual-") as temp_dir:
        temp_config = Path(temp_dir) / "run_config.json"
        compose_report = Path(temp_dir) / "compose_report.json"
        temp_config.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(PACKAGE_ROOT / "tools" / "compose_cards.py"), str(temp_config), "--report", str(compose_report)],
            check=False,
            text=True,
            capture_output=True,
        )
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout or "COMPOSER_UNAVAILABLE")
        reports = json.loads(compose_report.read_text(encoding="utf-8"))

    for report, card in zip(reports, config["cards"]):
        report["target_language"] = profile["locale"]
        report["language_profile"] = str(profile_path.relative_to(PACKAGE_ROOT))
        report["language_profile_status"] = profile["status"]
        report["style_reference"] = ref
        report["style_reference_sha256"] = actual_sha
        report["style_reference_attached"] = True
        report["platform"] = config.get("platform", "openai")
        report["font_files"] = sorted({value for value in fonts.values() if isinstance(value, str)})
        report["labels_text"] = [
            {
                "source_id": label.get("source_id"),
                "source_form": label.get("term"),
                "rendered_form": unicodedata.normalize("NFC", target_form(label)),
                "reading": unicodedata.normalize("NFC", pronunciation_text(label)),
                "gloss": gloss_fields(label)[0],
            }
            for label in card["labels"]
        ]
    report_path = config.get("report", str(config_dir / "multilingual_compose_report.json"))
    report_path = Path(report_path)
    if not report_path.is_absolute():
        report_path = config_dir / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    print(result.stdout.strip())
    print("multilingual report:", report_path)
    print("profile:", profile["locale"], "status:", profile["status"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Multilingual run_config.json")
    args = parser.parse_args()
    try:
        compose(args.config)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
