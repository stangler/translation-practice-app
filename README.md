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
├── .gitignore
├── .devcontainer/
│   ├── Dockerfile
│   └── devcontainer.json
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

```env
# Gemini（Google AI Studio）: https://aistudio.google.com/apikey
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.0-flash

# OpenRouter: https://openrouter.ai/settings/keys
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=openrouter/free
```

- `GEMINI_MODEL` / `OPENROUTER_MODEL` は省略可（デフォルト値を使用）
- どちらも設定しない場合は AI フォールバックなしで動作する

## 使い方

### 1. JSONをビルド（AIフォールバックなし）

```bash
uv run build.py xlsx/EIGO_NO_PARTNERに出てくる文.xlsx
```

`json/words-data.js` が生成される。そのまま `index.html` をブラウザで開けば動作する（AI判定は無効）。

### 2. dist/ をビルド（AIフォールバックあり）

```bash
uv run build.py xlsx/EIGO_NO_PARTNERに出てくる文.xlsx --dist
```

`dist/index.html` と `dist/json/words-data.js` が生成される。

### 3. ローカルサーバーで実行（推奨）

**重要：AIフォールバックを使う場合、ブラウザのセキュリティ制限により `file://` でのfetch呼び出しが禁止されるため、ローカルサーバーが必須です。**

```bash
# サーバー起動（dist/ を配信）
uv run python -m http.server 8080 --directory dist
```

ブラウザで `http://localhost:8080` を開く。

---

### dist/ について

- `--dist` オプション で `.env` から APIキーを読み込んで `dist/index.html` に埋め込む
- `.env` が存在しない場合は空文字を埋め込み、AI フォールバックは無効になる
- `dist/` は `.gitignore` に入っているため Git に含まれない

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

段階的に判定し、いずれかにマッチすれば正解。既存ロジックで不正解の場合のみ AI に問い合わせ。

| ステップ | 内容 | AI呼び出し |
|----------|------|-----------|
| 1 | NFKC正規化・記号除去・スペース除去後に完全一致 | ✗ |
| 2 | 文末表現（です／ます／だ 等）を除去した幹同士が一致 | ✗ |
| 3 | 同義語グループで正規化後に幹同士が一致 | ✗ |
| 3b | 正解が「、」区切りの複数語義の場合、いずれか1つに一致 | ✗ |
| 4 | kuromoji（形態素解析）による読み比較 | ✗ |
| 5 | **AI APIによる意味判定**（Gemini / OpenRouter） | ✓ |

### AI判定について（step 5）

既存ロジック（step 1〜4）で正解・不正解が判定できない場合のみ、AI APIに問い合わせ。

- **判定対象**：語順差（`毎日英語を` vs `英語を毎日`）、助詞差（`に行く` vs `へ行く`）、表現差（`上手に踊ることができます` vs `踊ることができます`）等
- **APIプロバイダー優先順位**：Gemini → OpenRouter
- **レスポンス形式**：YES / NO のみを期待
- **回答表示**：AI判定で正解時に「🤖 AI判定」バッジを表示

### 同義語グループ（抜粋）

| グループ | 例 |
|----------|----|
| 人称 | ぼく ／ わたし ／ 私 |
| 読む系 | 読む ／ 読みます ／ よむ ／ を読む ／ よみます など |
| 否定 | そうではありません ／ ちがいます ／ 違います |
| 見る系 | 見る ／ 見ます ／ みる ／ みます ／ を見る など |
| 演奏 | 演奏 ／ ひく |
| 球技 | バスケット ／ バスケットボール など |
| 曜日 | 月曜 ／ 月曜日 など |
| その他 | 学生／生徒、勉強／学習、上手／得意、親友／良い友達 など |

## 正解判定ルール（日→英）

NFKC正規化・小文字化・アポストロフィ統一後に完全一致。

---

## 開発環境（DevContainer）

Visual Studio Code + DevContainer で、自動的に Python + uv 環境を構築。

```bash
# DevContainer内での動作確認
uv run build.py xlsx/EIGO_NO_PARTNERに出てくる文.xlsx --dist
uv run python -m http.server 8080 --directory dist
```

## 今後の検討課題

- ユーザー認証・学習履歴保存（Next.js化による全面刷新を検討中）
- スコア・学習進捗の可視化
- チームモード（複数ユーザーの共有練習）
- モバイル最適化