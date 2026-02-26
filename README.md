# DocsWriter

DocsWriter is an open-source Python script for simulating a natural typing session in editors such as Google Docs or Microsoft Word.

## Features

- Types text with variable timing and pauses.
- Simulates occasional false starts.
- Introduces realistic typo behavior (neighbor-key mistakes, shift misses, accent simplification).
- Adds momentum-based typing speed changes while drafting.
- Includes small/big "thinking" breaks between sentences and paragraphs.
- Leaves a small number of permanent typos for more natural revision traces.
- Performs a second pass to correct selected words.
- Uses OpenAI to generate short "rethink" sentence starts.

## Files

- `docs_writer.py` – main automation script.

## Requirements

- Python 3.9+
- Desktop session where keyboard automation is allowed
- Packages:
  - `pyautogui`
  - `pyperclip`
  - `openai`

Install dependencies:

```bash
pip install pyautogui pyperclip openai
```

## Setup

1. Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your_openai_api_key"
```

2. Open `docs_writer.py` and paste your content into `TEXT_TO_WRITE`.

## Usage

Run the script:

```bash
python docs_writer.py
```

After launching, you have 5 seconds to focus the target document window. The script then types your text and performs a correction pass.

## Configuration

You can tune behavior at the top of `docs_writer.py`:

- `WRITING_TIME_MINUTES`
- `MAX_SMALL_BREAK_SECS`
- `MAX_BIG_BREAK_SECS`
- `GHOST_SENTENCE_CHANCE`
- `PLANNED_ERROR_RATE`
- `CORRECTED_TYPO_RATE`
- `PERMANENT_TYPO_RATE`
- `SHIFT_MISS_RATE`

## Safety Notes

- Keyboard/mouse automation can interfere with your normal input while running.
- Test in a disposable document first.
- Keep your API key in environment variables; do not hard-code secrets.
