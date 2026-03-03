import os
import re
import subprocess
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

ROOT = Path(__file__).parent
SCRIPT_PATH = ROOT / "docs_writer.py"
ENV_PATH = ROOT / ".env"


DEFAULTS = {
    "WRITING_TIME_MINUTES": "45",
    "MAX_SMALL_BREAK_SECS": "30",
    "MAX_BIG_BREAK_SECS": "120",
    "GHOST_SENTENCE_CHANCE": "0.15",
    "PLANNED_ERROR_RATE": "0.05",
    "PERMANENT_TYPO_RATE": "0.01",
    "CORRECTED_TYPO_RATE": "0.02",
    "SHIFT_MISS_RATE": "0.03",
}


def read_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def write_env_file(path: Path, data: dict[str, str]) -> None:
    lines = [f"{k}={data[k]}" for k in sorted(data.keys())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_profiles() -> dict[str, dict[str, str]]:
    env = read_env_file(ENV_PATH)
    profiles: dict[str, dict[str, str]] = {}
    for k, v in env.items():
        if k.startswith("OPENAI_API_KEY_"):
            name = k.replace("OPENAI_API_KEY_", "")
            profiles[name] = {
                "key": v,
                "model": env.get(f"OPENAI_MODEL_{name}", "gpt-4o-mini"),
            }
    return profiles


class DocsWriterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("DocsWriter Desktop")
        self.root.geometry("980x700")
        self.current_file: Path | None = None

        self.style = ttk.Style()
        self.style.theme_use("clam")

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root)
        top.pack(side=tk.TOP, fill=tk.X)

        self.tabs = ttk.Notebook(top)
        self.tabs.pack(fill=tk.X, padx=8, pady=8)

        self._build_file_tab()
        self._build_run_tab()
        self._build_settings_tab()

        editor_frame = ttk.Frame(self.root)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.editor = tk.Text(editor_frame, wrap=tk.WORD, undo=True, font=("Consolas", 11))
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(editor_frame, orient=tk.VERTICAL, command=self.editor.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor.configure(yscrollcommand=scroll.set)

        bottom = ttk.Frame(self.root)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)
        ttk.Button(bottom, text="Run DocsWriter", command=self.run_script).pack(fill=tk.X)
        self.status = ttk.Label(bottom, text="Ready")
        self.status.pack(anchor=tk.W, pady=(6, 0))

    def _build_file_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="File")

        ttk.Button(tab, text="New", command=self.new_file).pack(side=tk.LEFT, padx=6, pady=6)
        ttk.Button(tab, text="Load", command=self.load_file).pack(side=tk.LEFT, padx=6, pady=6)
        ttk.Button(tab, text="Save", command=self.save_file).pack(side=tk.LEFT, padx=6, pady=6)
        ttk.Button(tab, text="Save As", command=self.save_as_file).pack(side=tk.LEFT, padx=6, pady=6)

    def _build_run_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Run")

        self.profile_var = tk.StringVar(value="DEFAULT")
        self.param_vars = {k: tk.StringVar(value=v) for k, v in DEFAULTS.items()}

        row = 0
        ttk.Label(tab, text="Profile").grid(row=row, column=0, sticky="w", padx=6, pady=4)
        self.profile_combo = ttk.Combobox(tab, textvariable=self.profile_var, state="readonly", width=24)
        self.refresh_profiles()
        self.profile_combo.grid(row=row, column=1, sticky="w", padx=6, pady=4)

        for key in DEFAULTS:
            row += 1
            ttk.Label(tab, text=key).grid(row=row, column=0, sticky="w", padx=6, pady=4)
            ttk.Entry(tab, textvariable=self.param_vars[key], width=24).grid(row=row, column=1, sticky="w", padx=6, pady=4)

    def _build_settings_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Settings")

        ttk.Label(tab, text="Theme").pack(anchor=tk.W, padx=6, pady=(6, 2))
        self.theme_var = tk.StringVar(value="light")
        ttk.Radiobutton(tab, text="Light", variable=self.theme_var, value="light", command=self.apply_theme).pack(anchor=tk.W, padx=12)
        ttk.Radiobutton(tab, text="Dark", variable=self.theme_var, value="dark", command=self.apply_theme).pack(anchor=tk.W, padx=12)
        ttk.Button(tab, text="Manage API Keys", command=self.open_api_manager).pack(anchor=tk.W, padx=6, pady=8)

    def apply_theme(self) -> None:
        dark = self.theme_var.get() == "dark"
        bg = "#1f1f1f" if dark else "white"
        fg = "#f2f2f2" if dark else "black"
        self.editor.configure(bg=bg, fg=fg, insertbackground=fg)

    def refresh_profiles(self) -> None:
        profiles = sorted(load_profiles().keys())
        if not profiles:
            profiles = ["DEFAULT"]
        self.profile_combo["values"] = profiles
        if self.profile_var.get() not in profiles:
            self.profile_var.set(profiles[0])

    def new_file(self) -> None:
        self.editor.delete("1.0", tk.END)
        self.current_file = None
        self.status.configure(text="New file")

    def load_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not path:
            return
        content = Path(path).read_text(encoding="utf-8")
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", content)
        self.current_file = Path(path)
        self.status.configure(text=f"Loaded {self.current_file.name}")

    def save_file(self) -> None:
        if self.current_file is None:
            self.save_as_file()
            return
        self.current_file.write_text(self.editor.get("1.0", tk.END).rstrip("\n"), encoding="utf-8")
        self.status.configure(text=f"Saved {self.current_file.name}")

    def save_as_file(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not path:
            return
        self.current_file = Path(path)
        self.save_file()

    def open_api_manager(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Manage API Keys")
        win.geometry("440x240")

        profile_var = tk.StringVar(value="DEFAULT")
        key_var = tk.StringVar()
        model_var = tk.StringVar(value="gpt-4o-mini")

        ttk.Label(win, text="Profile Name").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(win, textvariable=profile_var, width=30).grid(row=0, column=1, padx=8, pady=6)

        ttk.Label(win, text="API Key").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(win, textvariable=key_var, width=30, show="*").grid(row=1, column=1, padx=8, pady=6)

        ttk.Label(win, text="Model").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(win, textvariable=model_var, width=30).grid(row=2, column=1, padx=8, pady=6)

        def save_profile() -> None:
            profile = profile_var.get().strip().upper()
            if not profile or not key_var.get().strip():
                messagebox.showerror("Missing values", "Profile and API key are required.")
                return
            env = read_env_file(ENV_PATH)
            env[f"OPENAI_API_KEY_{profile}"] = key_var.get().strip()
            env[f"OPENAI_MODEL_{profile}"] = model_var.get().strip() or "gpt-4o-mini"
            write_env_file(ENV_PATH, env)
            self.refresh_profiles()
            self.profile_var.set(profile)
            self.status.configure(text=f"Saved profile {profile} in .env")
            win.destroy()

        ttk.Button(win, text="Save", command=save_profile).grid(row=3, column=1, sticky="e", padx=8, pady=10)

    def run_script(self) -> None:
        text = self.editor.get("1.0", tk.END).strip()
        if not text:
            messagebox.showerror("Missing text", "Please enter text to write.")
            return
        profiles = load_profiles()
        profile_name = self.profile_var.get().strip().upper()
        profile = profiles.get(profile_name)
        if not profile:
            messagebox.showerror("Missing profile", "Set an API key profile in Settings > Manage API Keys.")
            return

        source = SCRIPT_PATH.read_text(encoding="utf-8")
        source = self.replace_vars(source)
        source = self.replace_text_block(source, text)
        source = self.replace_model(source, profile.get("model", "gpt-4o-mini"))

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py", encoding="utf-8") as temp:
            temp.write(source)
            temp_path = temp.name

        def execute() -> None:
            self.status.configure(text="Running script... focus target document in 5 seconds.")
            env = os.environ.copy()
            env["OPENAI_API_KEY"] = profile["key"]
            try:
                subprocess.run(["python", temp_path], env=env, check=True)
                self.status.configure(text="Run completed successfully")
            except subprocess.CalledProcessError as exc:
                self.status.configure(text=f"Run failed: {exc}")
                messagebox.showerror("Run failed", str(exc))
            finally:
                Path(temp_path).unlink(missing_ok=True)

        threading.Thread(target=execute, daemon=True).start()

    def replace_model(self, script: str, model: str) -> str:
        return re.sub(r'^MODEL_ID\s*=\s*".*?".*$', f'MODEL_ID = "{model}"', script, flags=re.MULTILINE)

    def replace_vars(self, script: str) -> str:
        for key, var in self.param_vars.items():
            script = re.sub(rf"^{key}\s*=\s*.*$", f"{key} = {var.get().strip()}", script, flags=re.MULTILINE)
        return script

    def replace_text_block(self, script: str, text: str) -> str:
        safe = text.replace('"""', '\\\"\\\"\\\"')
        replacement = f'TEXT_TO_WRITE = """\n{safe}\n"""'
        return re.sub(r'TEXT_TO_WRITE\s*=\s*"""[\s\S]*?"""', replacement, script, flags=re.MULTILINE)


if __name__ == "__main__":
    root = tk.Tk()
    DocsWriterApp(root)
    root.mainloop()
