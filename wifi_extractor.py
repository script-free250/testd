"""
WiFi Credential Extractor
==========================
Educational Purpose Only — For use on your own devices only.
Extracts saved WiFi profile names and passwords stored locally
on a Windows machine using the built-in `netsh` command.

Author  : Generated for educational use
Platform: Windows only
"""

import subprocess
import sys
import os
import csv
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime


# ──────────────────────────────────────────────
# Core Logic: WiFi Extraction via netsh
# ──────────────────────────────────────────────

def get_wifi_profiles() -> list[str]:
    """
    Retrieve all saved WiFi profile names on this Windows machine.
    Returns a list of SSID strings.
    """
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "profiles"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        profiles = []
        for line in result.stdout.splitlines():
            # Line format: "    All User Profile     : ProfileName"
            if "All User Profile" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    profiles.append(parts[1].strip())
        return profiles
    except FileNotFoundError:
        messagebox.showerror(
            "Error",
            "netsh command not found.\nThis program runs on Windows only."
        )
        return []
    except Exception as e:
        messagebox.showerror("Error", f"Failed to retrieve profiles:\n{e}")
        return []


def get_wifi_password(profile_name: str) -> str:
    """
    Given a WiFi profile name, retrieve its stored plain-text key (password).
    Returns the password string or a descriptive status string.
    """
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "profile",
             f"name={profile_name}", "key=clear"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        for line in result.stdout.splitlines():
            # Line format: "    Key Content            : MyPassword123"
            if "Key Content" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    return parts[1].strip()
        # If no key content line, the network likely uses enterprise auth
        # or has no password (open network)
        if "Authentication" in result.stdout:
            for line in result.stdout.splitlines():
                if "Authentication" in line and "Open" in line:
                    return "<Open Network — No Password>"
        return "<No Password / Enterprise Auth>"
    except Exception as e:
        return f"<Error: {e}>"


def extract_all_credentials() -> list[dict]:
    """
    Master function: fetch all profiles and their passwords.
    Returns a list of dicts: [{"ssid": "...", "password": "..."}, ...]
    """
    profiles = get_wifi_profiles()
    credentials = []
    for profile in profiles:
        password = get_wifi_password(profile)
        credentials.append({
            "ssid": profile,
            "password": password
        })
    return credentials


# ──────────────────────────────────────────────
# Export Helpers
# ──────────────────────────────────────────────

def export_to_csv(credentials: list[dict], filepath: str) -> None:
    """Save credentials list to a CSV file."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ssid", "password"])
        writer.writeheader()
        writer.writerows(credentials)


def export_to_json(credentials: list[dict], filepath: str) -> None:
    """Save credentials list to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(credentials, f, indent=4, ensure_ascii=False)


def export_to_txt(credentials: list[dict], filepath: str) -> None:
    """Save credentials list to a plain text file."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"WiFi Credentials — Exported {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        for item in credentials:
            f.write(f"SSID     : {item['ssid']}\n")
            f.write(f"Password : {item['password']}\n")
            f.write("-" * 40 + "\n")


# ──────────────────────────────────────────────
# GUI — Tkinter Interface
# ──────────────────────────────────────────────

class WiFiExtractorApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # ── Window setup ──
        self.title("WiFi Credential Extractor — Educational Use Only")
        self.geometry("780x520")
        self.resizable(True, True)
        self.configure(bg="#1e1e2e")

        # Store extracted data
        self.credentials: list[dict] = []

        self._build_ui()

    # ── UI Construction ────────────────────────

    def _build_ui(self):
        """Assemble all UI widgets."""

        # ── Title bar ──
        title_frame = tk.Frame(self, bg="#181825", pady=10)
        title_frame.pack(fill="x")

        tk.Label(
            title_frame,
            text="📡  WiFi Credential Extractor",
            font=("Segoe UI", 16, "bold"),
            bg="#181825",
            fg="#cdd6f4"
        ).pack(side="left", padx=20)

        tk.Label(
            title_frame,
            text="⚠️  Educational Use Only",
            font=("Segoe UI", 10),
            bg="#181825",
            fg="#f38ba8"
        ).pack(side="right", padx=20)

        # ── Button toolbar ──
        toolbar = tk.Frame(self, bg="#1e1e2e", pady=8)
        toolbar.pack(fill="x", padx=15)

        btn_style = {
            "font": ("Segoe UI", 10, "bold"),
            "relief": "flat",
            "cursor": "hand2",
            "padx": 16,
            "pady": 6,
            "bd": 0
        }

        self.btn_scan = tk.Button(
            toolbar,
            text="🔍  Scan WiFi Networks",
            bg="#89b4fa",
            fg="#1e1e2e",
            command=self._on_scan,
            **btn_style
        )
        self.btn_scan.pack(side="left", padx=(0, 8))

        self.btn_export = tk.Button(
            toolbar,
            text="💾  Export",
            bg="#a6e3a1",
            fg="#1e1e2e",
            command=self._on_export,
            state="disabled",
            **btn_style
        )
        self.btn_export.pack(side="left", padx=(0, 8))

        self.btn_clear = tk.Button(
            toolbar,
            text="🗑️  Clear",
            bg="#585b70",
            fg="#cdd6f4",
            command=self._on_clear,
            **btn_style
        )
        self.btn_clear.pack(side="left")

        # Status label (right side of toolbar)
        self.status_var = tk.StringVar(value="Ready — Press 'Scan' to begin.")
        tk.Label(
            toolbar,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg="#1e1e2e",
            fg="#a6adc8"
        ).pack(side="right")

        # ── Treeview table ──
        table_frame = tk.Frame(self, bg="#1e1e2e")
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 5))

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")

        # Style the treeview
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Custom.Treeview",
            background="#313244",
            foreground="#cdd6f4",
            fieldbackground="#313244",
            rowheight=28,
            font=("Consolas", 10)
        )
        style.configure(
            "Custom.Treeview.Heading",
            background="#45475a",
            foreground="#cdd6f4",
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", "#585b70")]
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=("no", "ssid", "password"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="Custom.Treeview"
        )

        # Column definitions
        self.tree.heading("no",       text="#")
        self.tree.heading("ssid",     text="Network Name (SSID)")
        self.tree.heading("password", text="Password")

        self.tree.column("no",       width=45,  minwidth=40,  anchor="center", stretch=False)
        self.tree.column("ssid",     width=300, minwidth=150, anchor="w")
        self.tree.column("password", width=380, minwidth=150, anchor="w")

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # ── Progress bar ──
        self.progress = ttk.Progressbar(
            self, mode="indeterminate", length=200
        )
        self.progress.pack(fill="x", padx=15, pady=(0, 8))

        # ── Footer ──
        tk.Label(
            self,
            text="Use this tool only on networks and devices you own. Unauthorized access is illegal.",
            font=("Segoe UI", 8),
            bg="#1e1e2e",
            fg="#585b70"
        ).pack(pady=(0, 6))

    # ── Event Handlers ─────────────────────────

    def _on_scan(self):
        """Trigger WiFi scan in a non-blocking way."""
        self.btn_scan.config(state="disabled")
        self.btn_export.config(state="disabled")
        self.status_var.set("Scanning… please wait.")
        self.progress.start(10)
        # Use after() to keep the UI responsive
        self.after(100, self._do_scan)

    def _do_scan(self):
        """Perform the actual scan and populate the table."""
        self.credentials = extract_all_credentials()
        self._populate_table()
        self.progress.stop()
        count = len(self.credentials)
        self.status_var.set(f"✅  Found {count} saved network(s).")
        self.btn_scan.config(state="normal")
        if count > 0:
            self.btn_export.config(state="normal")

    def _populate_table(self):
        """Clear and re-fill the Treeview with current credentials."""
        # Remove old rows
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Insert new rows with alternating row tags for readability
        for i, item in enumerate(self.credentials, start=1):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "", "end",
                values=(i, item["ssid"], item["password"]),
                tags=(tag,)
            )
        # Subtle zebra striping
        self.tree.tag_configure("odd",  background="#313244")
        self.tree.tag_configure("even", background="#2a2a3d")

    def _on_export(self):
        """Open a save dialog and export credentials to chosen format."""
        if not self.credentials:
            messagebox.showwarning("No Data", "Nothing to export. Run a scan first.")
            return

        filepath = filedialog.asksaveasfilename(
            title="Save Credentials",
            defaultextension=".csv",
            filetypes=[
                ("CSV File",  "*.csv"),
                ("JSON File", "*.json"),
                ("Text File", "*.txt"),
            ]
        )
        if not filepath:
            return  # User cancelled

        ext = os.path.splitext(filepath)[1].lower()
        try:
            if ext == ".csv":
                export_to_csv(self.credentials, filepath)
            elif ext == ".json":
                export_to_json(self.credentials, filepath)
            elif ext == ".txt":
                export_to_txt(self.credentials, filepath)
            else:
                export_to_csv(self.credentials, filepath)

            messagebox.showinfo(
                "Export Successful",
                f"Credentials saved to:\n{filepath}"
            )
            self.status_var.set(f"Exported → {os.path.basename(filepath)}")
        except PermissionError:
            messagebox.showerror("Permission Denied", f"Cannot write to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _on_clear(self):
        """Clear the table and reset state."""
        self.credentials = []
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.btn_export.config(state="disabled")
        self.status_var.set("Cleared. Press 'Scan' to begin.")


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

def main():
    """Application entry point."""
    # Quick platform check — netsh is Windows-only
    if sys.platform != "win32":
        # Still launch UI but show a warning
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Unsupported Platform",
            "This application requires Windows.\n"
            "The netsh command is not available on this OS."
        )
        sys.exit(1)

    app = WiFiExtractorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
