# 🐍 Razer DeathAdder Essential — DPI Changer v1.0.0

The first release of a lightweight, standalone DPI configuration utility for the Razer DeathAdder Essential.

Configure and read your mouse DPI directly through USB HID communication without installing or running Razer Synapse.

### ✨ Features

- **Synapse-Free Configuration:** Communicates directly with the mouse over USB HID.
- **Persistent DPI Settings:** Saves DPI configurations to onboard non-volatile memory (flash).
- **Live DPI Readout:** Reads and verifies the currently configured DPI using the device's `0x85` command.
- **Full DPI Range:** Supports 100–6400 DPI in 100 DPI increments.
- **Quick Presets:** One-click DPI selection for 400, 800, 1200, 1600, 3200, and 6400 DPI.
- **Modern GUI:** Cyber-themed dark interface built with Python Tkinter.

### 🖱️ Supported Devices

| Mouse Model | USB VID | USB PID | Status |
|---|---|---|---|
| Razer DeathAdder Essential | `0x1532` | `0x006E` | Supported |
| Razer DeathAdder Essential (2021/V2) | `0x1532` | `0x0098` | Tested & Confirmed |

### 📦 Installation

1. Download `Razer_DPI_Changer.exe` from the Assets section below.
2. Run the executable on Windows 10 or Windows 11.
3. Connect your supported Razer DeathAdder Essential mouse.
4. Select your preferred DPI or use one of the quick presets.

**Important:** Close Razer Synapse completely before launching the application if it is accessing the mouse's USB HID interface.

If you encounter USB HID permission or access issues, try running the application as Administrator.

### 🔧 Technical Details

- USB HID Feature Reports (90-byte protocol)
- GET DPI command: `0x85`
- SET DPI command: `0x05`
- Onboard storage target: `0x01`
- XOR checksum validation

### ⚠️ Compatibility Notice

This release is primarily intended for the supported Razer DeathAdder Essential models listed above. Other Razer devices have not been confirmed to work.

### 🤝 Feedback & Contributions

Found a bug or tested the application with another Razer mouse? Contributions, bug reports, and pull requests are welcome.

### 📜 License

Released under the MIT License.

---

**Thank you for checking out Razer DeathAdder Essential DPI Changer!**
