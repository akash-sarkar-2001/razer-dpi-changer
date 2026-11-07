# 🐍 Razer DeathAdder Essential — DPI Changer

A lightweight, standalone Python GUI tool to read and configure the DPI on your **Razer DeathAdder Essential** mouse directly over USB HID — **no Razer Synapse required**.

Settings are saved directly to the mouse's **onboard non-volatile memory (flash)**, meaning your DPI configuration **persists** even after closing the app, unplugging the mouse, or rebooting the PC.

---

## ✨ Features

- ⚡ **Synapse-Free**: Direct USB HID protocol communication. Zero bloatware running in the background.
- 💾 **Persistent DPI**: Writes to onboard non-volatile memory (`storage = 0x01`). Settings stick permanently until you change them again.
- 🔍 **Live DPI Readout**: Reads and verifies the current active DPI directly from the mouse sensor/MCU (`0x85` command).
- 🎚️ **Full Range Control**: Adjust sensitivity from **100 DPI** up to **6400 DPI** (in 100 DPI increments).
- 🚀 **Quick Presets**: 1-click buttons for common competitive DPI stages (`400`, `800`, `1200`, `1600`, `3200`, `6400`).
- 🎨 **Modern Cyber Dark UI**: Built with pure Python `tkinter` (no heavy GUI frameworks needed).

---

## 🖱️ Supported Hardware

| Device | USB Vendor ID | Product ID (PID) | Support Status |
|---|---|---|---|
| **Razer DeathAdder Essential** | `0x1532` | `0x006E` | Supported |
| **Razer DeathAdder Essential (2021/V2)** | `0x1532` | `0x0098` | Tested & Confirmed |

*(Other Razer mice using the standard 90-byte Razer feature report protocol may also work or require minor PID mapping).*

---

## 📋 Requirements

- **Operating System**: Windows 10 / 11, Linux, or macOS
- **Python**: 3.8 or higher
- **Dependencies**: [`hidapi`](https://pypi.org/project/hidapi/)

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/razer-dpi-changer.git
cd razer-dpi-changer
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application
```bash
python razer_dpi_changer.py
```

> **Note for Windows Users**: If Razer Synapse is currently running, exit it completely from the system tray first so it doesn't hold an exclusive lock on the USB HID interface. If you encounter permission errors, run your terminal/IDE as Administrator.

> **Note for Linux Users**: You may need to grant permission to access the raw USB device via a udev rule or run with `sudo`:
> ```bash
> sudo python3 razer_dpi_changer.py
> ```

---

## 🔬 How It Works (Protocol Details)

Razer USB devices communicate via 90-byte USB HID Feature Reports:

- **Report Structure**:
  - `byte[0]`: Report ID (`0x00`)
  - `byte[1]`: Status (`0x00` when sending; device returns `0x02` for `OK`)
  - `byte[2]`: Transaction ID (`0x1F` for DeathAdder Essential)
  - `byte[6]`: Command Class (`0x04` = Mouse)
  - `byte[7]`: Command ID (`0x85` for GET DPI, `0x05` for SET DPI)
  - `byte[8..14]`: Payload Arguments:
    - `args[0]`: Storage target (`0x01` = Onboard Flash / Non-volatile, `0x00` = RAM only)
    - `args[1..2]`: X DPI (Big Endian)
    - `args[3..4]`: Y DPI (Big Endian)
  - `byte[88]`: XOR Checksum across bytes 2–87

---

## 🤝 Contributing

Contributions, bug reports, and pull requests are welcome! If you test this on other Razer mouse models, feel free to submit an issue or PR updating the supported PIDs.

---

## 📜 License

MIT License. Free to use, modify, and distribute.
