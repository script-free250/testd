# 📡 WiFi Credential Extractor

> ⚠️ **Educational Use Only** — Use only on devices and networks you own.

A Windows desktop application that reads all **locally saved WiFi credentials**
using the built-in Windows `netsh wlan` command. No data is sent anywhere.

---

## 🖥️ Features

- 🔍 Scans all saved WiFi profiles on the local machine
- 🔑 Displays SSID + password in a clean GUI table
- 💾 Export to **CSV**, **JSON**, or **TXT**
- 🔐 SHA256 checksum included in every release
- 📦 Single `.exe` — no installation required
- 🤖 Fully automated build via **GitHub Actions**

---

## 📦 Usage

### Pre-built (recommended)
Download `WiFiExtractor.exe` from the [Releases](../../releases) page and run it.

### Build from source
```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/wifi-extractor.git
cd wifi-extractor

# 2. Install dependencies
pip install pyinstaller

# 3. Build the .exe
pyinstaller wifi_extractor.spec --distpath dist --noconfirm --clean

# 4. Run
dist\WiFiExtractor.exe
```

---

## 🤖 GitHub Actions — Auto Build

Every push to `main` triggers a build. The `.exe` is attached as an artifact.

### Create a versioned release:
```bash
git tag v1.0.0
git push origin v1.0.0
```
This auto-creates a GitHub Release with the `.exe` attached.

---

## 📋 Repository Structure

```
wifi-extractor/
├── wifi_extractor.py          # Main application source
├── wifi_extractor.spec        # PyInstaller build spec
├── README.md                  # This file
└── .github/
    └── workflows/
        └── build.yml          # GitHub Actions CI/CD workflow
```

---

## ⚖️ Legal Notice

This tool only reads credentials **already stored on your own machine**.
Using it on devices or networks you do not own is **illegal** under computer
access laws in most jurisdictions. The author assumes no liability.
