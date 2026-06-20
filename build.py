#!/usr/bin/env python3
"""
xlsx → words-data.js 変換スクリプト
列構成: Lesson / Part / 英語 / 日本語
"""

import json
import re
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
    header = rows[0]  # Lesson, Part, 英語, 日本語

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
            "ja_answers": ja_answers,  # 正解候補リスト
        })

    wb.close()

    js_content = f"const wordsData = {json.dumps(data, ensure_ascii=False, indent=2)};\n"
    out_path.write_text(js_content, encoding="utf-8")
    print(f"✓ {len(data)} 件出力 → {out_path}")


if __name__ == "__main__":
    xlsx = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data.xlsx")
    out = Path("json/words-data.js")
    build(xlsx, out)
