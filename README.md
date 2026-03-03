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
- `build_portable_zip.py` – creates a downloadable zip with bundled dependencies.

## Requirements (for development)

- Python 3.9+
- Python packages required by `docs_writer.py`:
  - `pyautogui`
  - `pyperclip`
  - `openai`

Install dependencies:

```bash
pip install pyautogui pyperclip openai
```

## Run from source

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

3. Launch:

```bash
python app.py
```

You can also create/edit profiles from **Settings > Manage API Keys**.

## Build a downloadable zip (includes deps + ready `.env`)

This creates a `dist/DocsWriterPortable.zip` archive that users can extract and run immediately.

```bash
python build_portable_zip.py
```

If your script is outside the project directory, point it explicitly:

```bash
python build_portable_zip.py --root "C:/path/to/DocsWriter"
```

The zip includes:

- `.venv` with all required dependencies preinstalled (`pyautogui`, `pyperclip`, `openai`)
- `app.py` and `docs_writer.py`
- pre-created `.env` (from `.env.example`)
- launchers:
  - `run-docswriter.sh` (macOS/Linux)
  - `run-docswriter.bat` (Windows)

User flow after download:

1. Unzip `DocsWriterPortable.zip`
2. Open `.env` and paste API key(s)
3. Run launcher (`run-docswriter.sh` or `run-docswriter.bat`)

## Notes

- Keep `.env` private and never commit real keys.
- Keyboard automation can interfere with normal input while running.
- Test with disposable documents first.
