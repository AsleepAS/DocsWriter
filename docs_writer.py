import os
import random
import re
import time

import pyautogui
import pyperclip
from openai import OpenAI

# --- 1. API CONFIGURATION ---
# Set your key before running:
#   export OPENAI_API_KEY="your_key"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_ID = "gpt-4o-mini"  # Fast and cost-effective for short "rethink" prompts.

# --- 2. WRITING SPEED CONFIG ---
WRITING_TIME_MINUTES = 45
MAX_SMALL_BREAK_SECS = 30
MAX_BIG_BREAK_SECS = 120

# --- 3. THE "HUMAN" VARIANTS ---
GHOST_SENTENCE_CHANCE = 0.15  # 15% chance to "rethink" a sentence start
PLANNED_ERROR_RATE = 0.05  # 5% of words typed wrong for the Phase 2 fix
PERMANENT_TYPO_RATE = 0.01  # 1% of typos are left uncorrected permanently
CORRECTED_TYPO_RATE = 0.02  # Immediate "fat-finger" corrections
SHIFT_MISS_RATE = 0.03  # Missing the shift key on capitals

# Proximity Map for realistic typos
KEYBOARD_NEIGHBORS = {
    "a": "qwsz",
    "b": "vghn",
    "c": "xdfv",
    "d": "serfcx",
    "e": "wsdrf",
    "f": "drtgvc",
    "g": "ftyhbv",
    "h": "gyujnb",
    "i": "ujko",
    "j": "hukmln",
    "k": "ijlm",
    "l": "okp",
    "m": "njk",
    "n": "bhjm",
    "o": "iklp",
    "p": "ol",
    "q": "aw",
    "r": "edftg",
    "s": "awedzx",
    "t": "rfghy",
    "u": "yhjkio",
    "v": "cfgbn",
    "w": "qase",
    "x": "zsdc",
    "y": "tghju",
    "z": "asx",
}

ACCENT_MAP = {
    "é": "e",
    "è": "e",
    "ê": "e",
    "ë": "e",
    "à": "a",
    "â": "a",
    "î": "i",
    "ï": "i",
    "ô": "o",
    "û": "u",
    "ù": "u",
    "ç": "c",
}


def get_ai_rethink(sentence):
    """Asks AI for a 'false start' variation of the sentence."""
    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {
                    "role": "system",
                    "content": "You are a student. Provide a realistic 5-8 word alternative start for this sentence. Return ONLY the text.",
                },
                {"role": "user", "content": f"Sentence: {sentence}"},
            ],
            max_tokens=15,
        )
        return response.choices[0].message.content.strip().replace('"', "")
    except Exception:
        return None


def get_typo(char):
    """Finds a key physically near the target key."""
    return random.choice(KEYBOARD_NEIGHBORS.get(char.lower(), "aeiou"))


def write_char(char):
    """Types characters, handling special accents via clipboard."""
    if char == " ":
        pyautogui.write(" ")
    elif char.isascii():
        pyautogui.write(char)
    else:
        pyperclip.copy(char)
        pyautogui.hotkey("ctrl", "v")


def human_type(text):
    pyautogui.FAILSAFE = True  # Move mouse to top-left to abort
    pyautogui.PAUSE = 0.01  # Tiny internal delay for stability

    paragraphs = text.split("\n\n")
    total_chars = len(text)
    repass_queue = []
    global_word_count = 0

    # Calculate base speed
    base_delay = (WRITING_TIME_MINUTES * 60) / (total_chars * 1.5)
    momentum = 1.0

    print("V6 RESTORED: Momentum & Break Logic Active. 5s to focus.")
    time.sleep(5)

    # --- PHASE 1: DRAFTING ---
    for p_idx, paragraph in enumerate(paragraphs):
        # 1. BIG BREAK LOGIC (Between Paragraphs)
        if p_idx > 0:
            pyautogui.press("enter", presses=2)
            momentum = 1.0  # Reset rhythm for new paragraph
            if random.random() < 0.7:
                break_duration = random.uniform(30, MAX_BIG_BREAK_SECS)
                print(f"Taking a big break: {int(break_duration)}s")
                time.sleep(break_duration)

        sentences = [s.strip() for s in re.split(r"(?<=[.!?]) +", paragraph) if s.strip()]

        for s_idx, sentence in enumerate(sentences):
            # 2. SMALL BREAK LOGIC (Mid-Paragraph "Thinking")
            if s_idx > 0 and random.random() < 0.15:
                break_duration = random.uniform(5, MAX_SMALL_BREAK_SECS)
                print(f"Thinking pause: {int(break_duration)}s")
                time.sleep(break_duration)

            # 1. GHOST RETHINK
            if random.random() < GHOST_SENTENCE_CHANCE:
                rethink = get_ai_rethink(sentence)
                if rethink:
                    to_type = rethink[: int(len(rethink) * random.uniform(0.4, 0.7))]
                    for c in to_type:
                        write_char(c)
                        time.sleep(random.uniform(0.1, 0.2))
                    time.sleep(random.uniform(1.5, 3))
                    for _ in range(len(to_type)):
                        pyautogui.press("backspace")
                        time.sleep(random.uniform(0.04, 0.06))

            # 2. WORD TYPING
            words = sentence.split(" ")
            for w_idx, word in enumerate(words):
                target_word = word

                # Assign Ghost Word (for later fix)
                if len(word) > 4 and random.random() < PLANNED_ERROR_RATE:
                    chars = list(word)
                    chars[-1], chars[-2] = chars[-2], chars[-1]  # Simple swap
                    target_word = "".join(chars)
                    repass_queue.append((global_word_count, word))

                for char in target_word:
                    current_delay = (base_delay / momentum) * random.uniform(0.8, 1.2)
                    rand = random.random()
                    if char.isupper() and rand < SHIFT_MISS_RATE:
                        write_char(char.lower())
                        time.sleep(0.3)
                        pyautogui.press("backspace")
                        write_char(char)
                        momentum = 1.0
                    elif rand < CORRECTED_TYPO_RATE and char.isalpha():
                        write_char(get_typo(char))
                        time.sleep(0.3)
                        pyautogui.press("backspace")
                        write_char(char)
                        momentum = 1.0
                    elif rand < PERMANENT_TYPO_RATE and char.isalpha():
                        write_char(get_typo(char))
                    elif char in ACCENT_MAP and rand < 0.04:
                        write_char(ACCENT_MAP[char])
                        momentum = min(4.5, momentum + 0.1)
                    else:
                        write_char(char)
                        momentum = min(4.5, momentum + 0.1)

                    if char in ".!?":
                        momentum = 1.0

                    time.sleep(current_delay)

                # Add a space unless it's the very end of the doc
                if not (
                    p_idx == len(paragraphs) - 1
                    and s_idx == len(sentences) - 1
                    and w_idx == len(words) - 1
                ):
                    write_char(" ")
                    momentum = max(1.0, momentum - 0.5)
                    time.sleep((base_delay / momentum) * random.uniform(0.5, 1.0))

                global_word_count += 1

            time.sleep(random.uniform(1, 3))

    # --- PHASE 2: THE REPASS (Correction) ---
    print(f"PHASE 2: Reviewing and correcting {len(repass_queue)} item(s)...")
    time.sleep(10)
    pyautogui.hotkey("ctrl", "home")

    current_pos = 0
    for error_idx, correction in repass_queue:
        # Navigate to the word
        while current_pos < error_idx:
            pyautogui.hotkey("ctrl", "right")
            current_pos += 1
            time.sleep(random.uniform(0.1, 0.2))

        # Perform the "Oh, there's a typo" correction
        time.sleep(random.uniform(1, 2.5))
        pyautogui.hotkey("ctrl", "shift", "left")
        time.sleep(0.4)
        pyautogui.press("backspace")
        for c in correction:
            write_char(c)
            time.sleep(random.uniform(0.05, 0.12))

        # Restore the space boundary
        write_char(" ")
        time.sleep(0.5)

    print("Document finalized.")


# ==========================================
# --- PASTE YOUR TEXT TO WRITE BELOW ---
# ==========================================
TEXT_TO_WRITE = """

"""

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: Set OPENAI_API_KEY before running.")
    elif not TEXT_TO_WRITE.strip() or "Your text here" in TEXT_TO_WRITE:
        print("ERROR: Please paste your text into TEXT_TO_WRITE at the bottom.")
    else:
        human_type(TEXT_TO_WRITE)
