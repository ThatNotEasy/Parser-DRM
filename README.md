# 🔐 DRM Device Parser

A Python-based utility for parsing and inspecting DRM device files, including **PlayReady**, **Widevine**, and **Widevine Keybox (binary/XML)** formats. The tool provides a clean CLI interface to identify, analyze, and decode device-level information with structured output.

---

## ✨ Features

- 📦 Supports multiple DRM file formats:
  - `.prd`, `.dat`, `.bin` → PlayReady
  - `.wvd` → Widevine
  - `.enc`, `.keybox`, `.bin` → Widevine Keybox (binary)
  - `.xml` → Widevine Keybox (XML)
- 📊 Pretty-printed terminal UI with color-coded output
- 🔍 Auto-detects device file versions and parses accordingly
- ✅ CRC checks and metadata decryption for Widevine Keyboxes
- 🧰 Modular structure for maintainability and extensibility

---

## 🧠 How It Works

1. Scans the `devices/` directory for supported device files.
2. Presents a UI for selecting which file to parse.
3. Automatically determines the DRM type and format.
4. Parses the file and displays structured results, including:
   - Device Name
   - Security Level
   - CRC Validity
   - Metadata Analysis
   - Device IDs and Certificates

---

## 🚀 Getting Started

### 🔧 Prerequisites

- Python 3.8+
- Install dependencies:

```bash
pip install -r requirements.txt
```

### 📂 Directory Setup

Create a `devices/` folder and drop your device files there:

```
Parser-DRM/
├── devices/
│   ├── sample_device.prd
│   ├── another_device.wvd
│   └── keybox_device.enc
│   └── keybox_device.xml
```

### ▶️ Run the Parser

```bash
python main.py
```

---

## 📁 Supported Formats

| Format Extension | DRM Type         | Description                        |
|------------------|------------------|------------------------------------|
| `.prd`, `.dat`   | PlayReady        | Device (CDM) files                 |
| `.wvd`           | Widevine         | L1/L3 Device (CDM) files           |
| `.keybox`, `.enc`| Widevine Keybox  | Binary Keybox with metadata        |
| `.xml`           | Widevine XML     | Keybox in XML format               |

---

## ⚠️ Disclaimer

This tool is intended for **educational and research purposes only**. Accessing or modifying DRM-protected data without authorization may violate laws or terms of service. Use responsibly.

---

## 💬 Feedback & Contributions

Feel free to open issues or submit PRs! Contributions, feature suggestions, and improvements are welcome. 🤝