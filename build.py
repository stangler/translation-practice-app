#!/usr/bin/env python3
"""
xlsx → words-data.js 変換スクリプト
列構成: Lesson / Part / 英語 / 日本語

オプション:
  --dist    .env の GEMINI_API_KEY を index.html に埋め込んで dist/ を生成
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path
import openpyxl


def parse_ja_answer(ja_text: str) -> list[str]:
    """
    日本語テキストから正解候補リストを生成する。
    例: 「私はネコを好みます。（=私はネコが好きです。）」
    → ["私はネコを好みます。", "私はネコが好きです。"]
    """
    if not ja_text:
        return []

    answers = []
    # メイン部分（括弧より前）
    main = re.sub(r'（[^）]*）', '', ja_text).strip()
    if main:
        answers.append(main)

    # 括弧内の =～ を抽出
    for m in re.finditer(r'（=([^）]+)）', ja_text):
        alt = m.group(1).strip()
        if alt and alt not in answers:
            answers.append(alt)

    return answers if answers else [ja_text]


def build(xlsx_path: Path, out_path: Path):
    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))

    data = []
    for row in rows[1:]:
        if not any(row):
            continue
        lesson_raw, part_raw, en, ja = row[0], row[1], row[2], row[3]

        if not en or not ja:
            continue

        lesson = str(lesson_raw).strip() if lesson_raw is not None else ""
        part = str(part_raw).strip() if part_raw is not None and str(part_raw).strip() != "" else ""
        # 数値のPartは整数文字列に正規化（例: 1.0 → "1"）
        try:
            part = str(int(float(part))) if part else ""
        except (ValueError, TypeError):
            pass  # 文字列Partはそのまま

        ja_str = str(ja).strip()
        en_str = str(en).strip()

        ja_answers = parse_ja_answer(ja_str)

        data.append({
            "lesson": lesson,
            "part": part,
            "en": en_str,
            "ja": ja_str,
            "ja_answers": ja_answers,
        })

    wb.close()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    js_content = f"const wordsData = {json.dumps(data, ensure_ascii=False, indent=2)};\n"
    out_path.write_text(js_content, encoding="utf-8")
    print(f"✓ {len(data)} 件出力 → {out_path}")


def parse_env_value(value: str) -> str:
    """値のインラインコメント（# 以降）を除去して返す"""
    return value.split("#")[0].strip()


def build_dist(src_html: Path = Path("index.html"), dist_dir: Path = Path("dist")):
    """
    index.html の __GEMINI_API_KEY__ を .env から読んだキーで置換して
    dist/index.html を生成する。words-data.js も dist/json/ にコピーする。
    """
    # .env 読み込み
    api_key = ""
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                api_key = parse_env_value(line.split("=", 1)[1])
                break



    # dist/ に index.html を出力
    dist_dir.mkdir(parents=True, exist_ok=True)
    content = src_html.read_text(encoding="utf-8")
    gemini_model = "gemini-2.0-flash"  # デフォルト
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("GEMINI_MODEL="):
                gemini_model = parse_env_value(line.split("=", 1)[1])
                break
    content = content.replace("__GEMINI_API_KEY__", api_key)
    content = content.replace("__GEMINI_MODEL__", gemini_model)

    openrouter_key = ""
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("OPENROUTER_API_KEY="):
                openrouter_key = parse_env_value(line.split("=", 1)[1])
                break
    if not openrouter_key and not api_key:
        print("⚠️  .env に GEMINI_API_KEY も OPENROUTER_API_KEY も見つかりません。AIフォールバックは無効になります。")
    content = content.replace("__OPENROUTER_API_KEY__", openrouter_key)

    openrouter_model = "google/gemini-2.0-flash-001"  # デフォルト
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("OPENROUTER_MODEL="):
                openrouter_model = parse_env_value(line.split("=", 1)[1])
                break
    content = content.replace("__OPENROUTER_MODEL__", openrouter_model)
    out_html = dist_dir / "index.html"
    out_html.write_text(content, encoding="utf-8")

    # words-data.js をコピー
    words_src = Path("json/words-data.js")
    if words_src.exists():
        words_dst = dist_dir / "json"
        words_dst.mkdir(parents=True, exist_ok=True)
        shutil.copy(words_src, words_dst / "words-data.js")
        print(f"✓ json/words-data.js → {words_dst}/words-data.js")

    ai_status = "Gemini" if api_key else ("OpenRouter" if openrouter_key else "無効")
    print(f"✅ dist/index.html を生成しました（AIフォールバック: {ai_status}）")


if __name__ == "__main__":
    args = sys.argv[1:]
    do_dist = "--dist" in args
    xlsx_args = [a for a in args if not a.startswith("--")]

    xlsx = Path(xlsx_args[0]) if xlsx_args else Path("data.xlsx")
    out = Path("json/words-data.js")

    build(xlsx, out)

    if do_dist:
        build_dist()
