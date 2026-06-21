# translation-practice-app

EIGO NO PARTNER に出てくる文の英語練習テストアプリ。

## 機能

- **英→日モード**：英語を見て日本語をタイピング
- **日→英モード**：日本語を見て英語をタイピング
- レッスン・パート単位で出題範囲を選択
- シャッフル機能
- あかぺん風の○✗アニメーション採点
- 間違い一覧・再挑戦機能
- **AI APIによる表記ゆれ吸収**（Gemini / OpenRouter 対応・オプション）

## ファイル構成

```
translation-practice-app/
├── index.html          # メインアプリ（プレースホルダー入り）
├── build.py            # xlsx → JSON 変換 ＋ dist/ 生成スクリプト
├── README.md
├── .env                # APIキー記載（Git管理外）
├── xlsx/
│   └── EIGO_NO_PARTNERに出てくる文.xlsx  # 元データ（Git管理外）
├── json/
│   └── words-data.js   # ビルド生成ファイル（Git管理外）
└── dist/               # ブラウザで開くファイル一式（Git管理外）
    ├── index.html      # APIキー埋め込み済み
    └── json/
        └── words-data.js
```

## セットアップ

### 必要環境

- Python 3.11+
- uv（パッケージ管理）

### 依存パッケージのインストール

```bash
uv pip install openpyxl
```

### AI APIキーの設定（オプション）

表記ゆれ・語順差などをAIで吸収したい場合のみ必要。Gemini と OpenRouter のどちらか一方、または両方設定できる。両方ある場合は Gemini が優先される。

プロジェクトルートに `.env` を作成：

```
# Gemini（Google AI Studio）: https://aistudio.google.com/apikey
GEMINI_API_KEY=AIzaSy...

# OpenRouter: https://openrouter.ai/settings/keys
OPENROUTER_API_KEY=sk-or-...
```

どちらも設定しない場合は AI フォールバックなしで動作する。

## 使い方

### 1. JSONをビルド（Geminiなし）

```powershell
uv run build.py xlsx/EIGO_NO_PARTNERに出てくる文.xlsx
```

`json/words-data.js` が生成される。そのまま `index.html` をブラウザで開けば動作する（Geminiフォールバックは無効）。

### 2. dist/ をビルド（AIフォールバックあり）

```powershell
uv run build.py xlsx/EIGO_NO_PARTNERに出てくる文.xlsx --dist
```

`dist/index.html` と `dist/json/words-data.js` が生成される。**`dist/index.html` をブラウザで開く。**

> `.env` が存在しない場合は AI フォールバックなしで動作する（既存ロジックのみ）。

---

## xlsxの列構成

| 列 | 内容 | 例 |
|----|------|----|
| A | Lesson | `Starter` / `1` / `2` / `3` |
| B | Part | `1` / `2` / `Goal Activity` / `学んだことを整理する1` など |
| C | 英語 | `I like cats.` |
| D | 日本語 | `私はネコを好みます。（=私はネコが好きです。）` |

### 複数正解の書き方

日本語列に `（=別解）` 形式で記載すると、どちらでも正解として扱われる。

```
私はネコを好みます。（=私はネコが好きです。）
```

## 正解判定ルール（英→日）

段階的に判定し、いずれかにマッチすれば正解。

| ステップ | 内容 |
|----------|------|
| 1 | NFKC正規化・記号除去・スペース除去後に完全一致 |
| 2 | 文末表現（です／ます／だ 等）を除去した幹同士が一致 |
| 3 | 同義語グループで正規化後に幹同士が一致 |
| 3b | 正解が「、」区切りの複数語義の場合、いずれか1つに一致 |
| 4 | kuromoji（形態素解析）による読み比較 |
| 5 | AI APIによる意味判定（Gemini / OpenRouter・APIキー設定時のみ） |

### 同義語グループ（抜粋）

| グループ | 例 |
|----------|----|
| 人称 | ぼく ／ わたし ／ 私 |
| 読む系 | 読む ／ 読みます ／ よむ ／ を読む など |
| 否定 | そうではありません ／ ちがいます ／ 違います |
| その他 | 学生／生徒、勉強／学習、上手／得意 など |

## 正解判定ルール（日→英）

NFKC正規化・小文字化・アポストロフィ統一後に完全一致。
