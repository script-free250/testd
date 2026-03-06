"""
WiFi Credential Extractor
==========================
Educational Purpose Only — For use on your own devices only.
Extracts saved WiFi profile names and passwords stored locally
on a Windows machine.

ROOT CAUSE FIX:
  The original code searched for English text labels like
  "All User Profile" and "Key Content" in the output of
  `netsh wlan show profiles`.

  On Arabic Windows (and any non-English Windows), netsh
  outputs these labels in the local language, so the English
  string search found nothing and the scan returned empty.

SOLUTION:
  Use `netsh wlan export profile key=clear` instead.
  This writes one XML file per saved network into a temp folder.
  The XML schema (element names, namespace) is ALWAYS in English
  regardless of Windows UI language, so parsing it works
  universally on any Windows locale.

Author  : Generated for educational use
Platform: Windows only
"""

import subprocess
import sys
import os
import csv
import json
import tempfile
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime


# ──────────────────────────────────────────────────────────────────────
# Core Logic — XML-based WiFi Extraction (Language Independent)
# ──────────────────────────────────────────────────────────────────────

# The official WLAN profile XML namespace — fixed, never localised
WLAN_NS = "http://www.microsoft.com/networking/WLAN/profile/v1"


def _xml_find(root: ET.Element, tag: str) -> ET.Element | None:
    """
    Find a child element by tag name using the WLAN namespace.
    Falls back to a namespace-less search for older profile formats.
    """
    elem = root.find(f".//{{{WLAN_NS}}}{tag}")
    if elem is None:
        elem = root.find(f".//{tag}")
    return elem


def _parse_profile_xml(filepath: str) -> dict | None:
    """
    Parse a single netsh-exported WiFi profile XML file.

    Returns {"ssid": str, "password": str} or None on parse failure.

    XML structure (abbreviated):
        <WLANProfile xmlns="...WLAN/profile/v1">
          <name>ProfileDisplayName</name>       ← used as display label
          <SSIDConfig>
            <SSID>
              <name>ActualSSID</name>            ← the real network name
            </SSID>
          </SSIDConfig>
          <MSM>
            <security>
              <authEncryption>
                <authentication>WPA2PSK</authentication>
              </authEncryption>
              <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>MyPassword123</keyMaterial>  ← plain password
              </sharedKey>
            </security>
          </MSM>
        </WLANProfile>
    """
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except ET.ParseError:
        return None  # Skip corrupted files silently

    # ── SSID name ─────────────────────────────────────────────────────
    # Prefer the <name> inside <SSID> (the real broadcast name)
    # Fall back to the top-level <name> (the Windows profile display name)
    ssid_elem = _xml_find(root, "SSID")
    if ssid_elem is not None:
        inner = _xml_find(ssid_elem, "name")
        ssid = inner.text.strip() if (inner is not None and inner.text) else None
    else:
        ssid = None

    if not ssid:
        top_name = _xml_find(root, "name")
        ssid = (
            top_name.text.strip()
            if (top_name is not None and top_name.text)
            else os.path.basename(filepath).replace(".xml", "")
        )

    # ── Password (keyMaterial) ─────────────────────────────────────────
    key_elem = _xml_find(root, "keyMaterial")

    if key_elem is not None and key_elem.text:
        password = key_elem.text.strip()
    else:
        # No keyMaterial — determine why for a helpful message
        auth_elem = _xml_find(root, "authentication")
        auth = auth_elem.text.strip() if (auth_elem is not None and auth_elem.text) else ""

        if auth.lower() in ("open", ""):
            password = "<Open Network — No Password>"
        elif "Enterprise" in auth:
            password = f"<{auth} — No Stored Key>"
        else:
            # WPA2PSK/WPA3 etc. but key wasn't exported (e.g. MDM-managed)
            password = "<Key Not Available>"

    return {"ssid": ssid, "password": password}


def extract_all_credentials() -> list[dict]:
    """
    Export every saved WiFi profile to XML, parse each file, and
    return a sorted list of {"ssid": ..., "password": ...} dicts.

    Uses a TemporaryDirectory so all exported files are auto-deleted
    when this function returns.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:

        # ── Step 1: Export all profiles to XML ────────────────────────
        # `key=clear` tells netsh to include the plaintext password.
        export = subprocess.run(
            [
                "netsh", "wlan", "export", "profile",
                f"folder={tmp_dir}",
                "key=clear",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        xml_files = [
            f for f in os.listdir(tmp_dir) if f.lower().endswith(".xml")
        ]

        # Hard failure: command returned non-zero AND produced no files
        if export.returncode != 0 and not xml_files:
            err = (export.stderr or export.stdout).strip()
            raise RuntimeError(
                f"netsh export failed (exit code {export.returncode}).\n\n"
                f"Details:\n{err or 'No details available.'}\n\n"
                "Make sure the WLAN AutoConfig service is running\n"
                "and that a wireless adapter is present."
            )

        if not xml_files:
            return []  # No profiles saved — return empty list normally

        # ── Step 2: Parse each XML file ───────────────────────────────
        credentials = []
        for filename in xml_files:
            result = _parse_profile_xml(os.path.join(tmp_dir, filename))
            if result is not None:
                credentials.append(result)

    # Sort alphabetically by SSID (case-insensitive) for readability
    credentials.sort(key=lambda x: x["ssid"].casefold())
    return credentials


# ──────────────────────────────────────────────────────────────────────
# Export Helpers
# ──────────────────────────────────────────────────────────────────────

def export_to_csv(credentials: list[dict], filepath: str) -> None:
    """Save credentials list to a CSV file (UTF-8 with BOM for Excel)."""
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
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
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"WiFi Credentials — Exported {timestamp}\n")
        f.write("=" * 60 + "\n\n")
        for item in credentials:
            f.write(f"SSID     : {item['ssid']}\n")
            f.write(f"Password : {item['password']}\n")
            f.write("-" * 40 + "\n")


# ──────────────────────────────────────────────────────────────────────
# GUI — Tkinter Interface
# ──────────────────────────────────────────────────────────────────────

class WiFiExtractorApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("WiFi Credential Extractor — Educational Use Only")
        self.geometry("780x520")
        self.resizable(True, True)
        self.configure(bg="#1e1e2e")

        self.credentials: list[dict] = []
        self._build_ui()

    # ── UI Construction ───────────────────────────────────────────────

    def _build_ui(self):
        """Assemble all UI widgets."""

        # Title bar
        title_frame = tk.Frame(self, bg="#181825", pady=10)
        title_frame.pack(fill="x")

        tk.Label(
            title_frame,
            text="📡  WiFi Credential Extractor",
            font=("Segoe UI", 16, "bold"),
            bg="#181825",
            fg="#cdd6f4",
        ).pack(side="left", padx=20)

        tk.Label(
            title_frame,
            text="⚠️  Educational Use Only",
            font=("Segoe UI", 10),
            bg="#181825",
            fg="#f38ba8",
        ).pack(side="right", padx=20)

        # Button toolbar
        toolbar = tk.Frame(self, bg="#1e1e2e", pady=8)
        toolbar.pack(fill="x", padx=15)

        btn_style = {
            "font": ("Segoe UI", 10, "bold"),
            "relief": "flat",
            "cursor": "hand2",
            "padx": 16,
            "pady": 6,
            "bd": 0,
        }

        self.btn_scan = tk.Button(
            toolbar,
            text="🔍  Scan WiFi Networks",
            bg="#89b4fa",
            fg="#1e1e2e",
            command=self._on_scan,
            **btn_style,
        )
        self.btn_scan.pack(side="left", padx=(0, 8))

        self.btn_export = tk.Button(
            toolbar,
            text="💾  Export",
            bg="#a6e3a1",
            fg="#1e1e2e",
            command=self._on_export,
            state="disabled",
            **btn_style,
        )
        self.btn_export.pack(side="left", padx=(0, 8))

        self.btn_clear = tk.Button(
            toolbar,
            text="🗑️  Clear",
            bg="#585b70",
            fg="#cdd6f4",
            command=self._on_clear,
            **btn_style,
        )
        self.btn_clear.pack(side="left")

        self.status_var = tk.StringVar(value="Ready — Press 'Scan' to begin.")
        tk.Label(
            toolbar,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg="#1e1e2e",
            fg="#a6adc8",
        ).pack(side="right")

        # Treeview table
        table_frame = tk.Frame(self, bg="#1e1e2e")
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 5))

        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Custom.Treeview",
            background="#313244",
            foreground="#cdd6f4",
            fieldbackground="#313244",
            rowheight=28,
            font=("Consolas", 10),
        )
        style.configure(
            "Custom.Treeview.Heading",
            background="#45475a",
            foreground="#cdd6f4",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map("Custom.Treeview", background=[("selected", "#585b70")])

        self.tree = ttk.Treeview(
            table_frame,
            columns=("no", "ssid", "password"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="Custom.Treeview",
        )

        self.tree.heading("no",       text="#")
        self.tree.heading("ssid",     text="Network Name (SSID)")
        self.tree.heading("password", text="Password")

        self.tree.column("no",       width=45,  minwidth=40,  anchor="center", stretch=False)
        self.tree.column("ssid",     width=300, minwidth=150, anchor="w")
        self.tree.column("password", width=380, minwidth=150, anchor="w")

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # Progress bar
        self.progress = ttk.Progressbar(self, mode="indeterminate", length=200)
        self.progress.pack(fill="x", padx=15, pady=(0, 8))

        # Footer
        tk.Label(
            self,
            text=(
                "Use this tool only on networks and devices you own. "
                "Unauthorized access is illegal."
            ),
            font=("Segoe UI", 8),
            bg="#1e1e2e",
            fg="#585b70",
        ).pack(pady=(0, 6))

    # ── Event Handlers ────────────────────────────────────────────────

    def _on_scan(self):
        """Start the scan — lock the button and show progress."""
        self.btn_scan.config(state="disabled")
        self.btn_export.config(state="disabled")
        self.status_var.set("Scanning… please wait.")
        self.progress.start(10)
        # Defer one frame so the UI repaints before the blocking call
        self.after(100, self._do_scan)

    def _do_scan(self):
        """Perform extraction and update the table. Called via after()."""
        try:
            self.credentials = extract_all_credentials()
            self._populate_table()
            count = len(self.credentials)
            if count > 0:
                self.status_var.set(f"✅  Found {count} saved network(s).")
                self.btn_export.config(state="normal")
            else:
                self.status_var.set("⚠️  No saved WiFi networks found on this machine.")
        except RuntimeError as exc:
            messagebox.showerror("Scan Failed", str(exc))
            self.status_var.set("❌  Scan failed — see error dialog.")
        except FileNotFoundError:
            messagebox.showerror(
                "Error",
                "netsh command not found.\nThis program runs on Windows only.",
            )
            self.status_var.set("❌  Windows required.")
        except Exception as exc:
            messagebox.showerror("Unexpected Error", f"{type(exc).__name__}:\n{exc}")
            self.status_var.set("❌  Scan failed.")
        finally:
            self.progress.stop()
            self.btn_scan.config(state="normal")

    def _populate_table(self):
        """Clear and re-fill the Treeview."""
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, item in enumerate(self.credentials, start=1):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "", "end",
                values=(i, item["ssid"], item["password"]),
                tags=(tag,),
            )
        self.tree.tag_configure("odd",  background="#313244")
        self.tree.tag_configure("even", background="#2a2a3d")

    def _on_export(self):
        """Open save dialog and export to the chosen format."""
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
            ],
        )
        if not filepath:
            return

        ext = os.path.splitext(filepath)[1].lower()
        try:
            if ext == ".json":
                export_to_json(self.credentials, filepath)
            elif ext == ".txt":
                export_to_txt(self.credentials, filepath)
            else:
                export_to_csv(self.credentials, filepath)

            messagebox.showinfo(
                "Export Successful",
                f"Credentials saved to:\n{filepath}",
            )
            self.status_var.set(f"Exported → {os.path.basename(filepath)}")
        except PermissionError:
            messagebox.showerror("Permission Denied", f"Cannot write to:\n{filepath}")
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    def _on_clear(self):
        """Clear the table and reset state."""
        self.credentials = []
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.btn_export.config(state="disabled")
        self.status_var.set("Cleared. Press 'Scan' to begin.")


# ──────────────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────────────

def main():
    """Application entry point."""
    if sys.platform != "win32":
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Unsupported Platform",
            "This application requires Windows.\n"
            "The netsh command is not available on this OS.",
        )
        sys.exit(1)

    app = WiFiExtractorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
