# DocsWriter

DocsWriter now includes a lightweight desktop app (`app.py`) that wraps the existing `docs_writer.py` script.

## What changed

- `docs_writer.py` is still the typing engine and was not edited.
- `app.py` provides a one-window notepad-like UI.
- Top hotbar tabs:
  - **File**: New, Load, Save, Save As
  - **Run**: profile selection + all run parameters
  - **Settings**: light/dark mode + API key manager
- API keys/models are stored in a separate `.env` file, with support for multiple profiles.

## Files

- `docs_writer.py` – original automation script.
- `app.py` – desktop application.
- `.env.example` – template for API key/model profiles.

## Requirements

- Python 3.9+
- Python packages required by `docs_writer.py`:
  - `pyautogui`
  - `pyperclip`
  - `openai`

Install dependencies:

```bash
pip install pyautogui pyperclip openai
```

## Setup

1. Copy and edit environment file:

```bash
cp .env.example .env
```

2. Add one or more profiles:

```dotenv
OPENAI_API_KEY_DEFAULT=sk-...
OPENAI_MODEL_DEFAULT=gpt-4o-mini
OPENAI_API_KEY_WORK=sk-...
OPENAI_MODEL_WORK=gpt-4.1-mini
```

You can also create/edit profiles from **Settings > Manage API Keys**.

## Run

```bash
python app.py
```

## Build as downloadable app (single file)

Install PyInstaller:

```bash
pip install pyinstaller
```

Build executable:

```bash
pyinstaller --onefile --windowed app.py
```

Output binary will be in `dist/` (for example `dist/app.exe` on Windows).
Distribute it with `docs_writer.py` and `.env` in the same folder.

## Notes

- Keep `.env` private and never commit real keys.
- Keyboard automation can interfere with normal input while running.
- Test with disposable documents first.
