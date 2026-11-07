#!/usr/bin/env python3
"""
Razer DeathAdder Essential — DPI Changer
Communicates directly with the mouse via USB HID (Razer protocol).
No Razer Synapse needed.

Usage:
    pip install hidapi
    python razer_dpi_changer.py

Note: On Windows you may need to run as Administrator if the device
      is locked by another driver.
"""

import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import hid
except ImportError:
    print("=" * 55)
    print("  Missing dependency: hidapi")
    print("  Install it with:  pip install hidapi")
    print("=" * 55)
    sys.exit(1)


# ── Razer USB Protocol Constants ────────────────────────────────────────────

RAZER_VENDOR_ID          = 0x1532
DEATHADDER_ESSENTIAL_PIDS = {
    0x006E: "DeathAdder Essential",
    0x0098: "DeathAdder Essential V2",
}

RAZER_REPORT_LEN  = 90
TRANSACTION_ID    = 0x1F   # Confirmed working for PID 0x0098

CMD_CLASS_MOUSE   = 0x04
CMD_SET_DPI       = 0x05   # SET uses 0x05
CMD_GET_DPI       = 0x85   # GET uses 0x85 (0x05 | 0x80) — confirmed via probing
DPI_DATA_SIZE     = 0x07

MIN_DPI           = 100
MAX_DPI           = 6400
DPI_STEP          = 100


# ── Razer Protocol Helpers ──────────────────────────────────────────────────

def _crc(buf: bytearray) -> int:
    """XOR bytes 2‑87 of the 90‑byte report."""
    crc = 0
    for i in range(2, 88):
        crc ^= buf[i]
    return crc


def build_report(command_class: int, command_id: int,
                 data_size: int, args: list[int] | None = None) -> bytes:
    """Build a 90‑byte Razer USB feature report."""
    buf = bytearray(RAZER_REPORT_LEN)
    buf[0] = 0x00                   # Status — new command
    buf[1] = TRANSACTION_ID         # Transaction ID
    buf[2] = 0x00                   # Remaining packets MSB
    buf[3] = 0x00                   # Remaining packets LSB
    buf[4] = 0x00                   # Protocol type
    buf[5] = data_size              # Data size
    buf[6] = command_class          # Command class
    buf[7] = command_id             # Command ID
    if args:
        for i, b in enumerate(args):
            buf[8 + i] = b
    buf[88] = _crc(buf)             # CRC
    buf[89] = 0x00                  # Reserved
    return bytes(buf)


def make_set_dpi(dpi_x: int, dpi_y: int) -> bytes:
    """Build a SET DPI command (command 0x05)."""
    return build_report(CMD_CLASS_MOUSE, CMD_SET_DPI, DPI_DATA_SIZE, [
        0x01,                        # Non-volatile (onboard memory)
        (dpi_x >> 8) & 0xFF,         # DPI X high byte
        dpi_x & 0xFF,                # DPI X low byte
        (dpi_y >> 8) & 0xFF,         # DPI Y high byte
        dpi_y & 0xFF,                # DPI Y low byte
        0x00,                        # Padding
        0x00,                        # Padding
    ])


def make_get_dpi() -> bytes:
    """Build a GET DPI command (command 0x85)."""
    return build_report(CMD_CLASS_MOUSE, CMD_GET_DPI, DPI_DATA_SIZE,
                        [0x00] * DPI_DATA_SIZE)


# ── Device Communication ───────────────────────────────────────────────────

class RazerDevice:
    """Thin wrapper around hidapi for Razer feature‑report I/O."""

    def __init__(self):
        self.handle: hid.device | None = None
        self.info: dict | None = None
        self.product_name: str = ""

    # ── connection ──────────────────────────────────────────────────────

    def find_interfaces(self) -> list[dict]:
        """Return all HID interfaces belonging to a DeathAdder Essential."""
        return [
            d for d in hid.enumerate(RAZER_VENDOR_ID)
            if d["product_id"] in DEATHADDER_ESSENTIAL_PIDS
        ]

    def connect(self) -> tuple[bool, str]:
        """
        Open the control interface (interface 0).

        Confirmed via probing that interface 0 (usage_page=0x0001,
        usage=0x0002) is the control interface for PID 0x0098.
        """
        candidates = self.find_interfaces()
        if not candidates:
            return False, ("Razer DeathAdder Essential not found.\n"
                           "Make sure it's plugged in via USB.")

        self.product_name = candidates[0].get("product_string",
                                               "DeathAdder Essential")

        # Prefer interface 0 (confirmed control interface)
        candidates.sort(key=lambda d: (d.get("interface_number", 99),))

        # Try to open and verify with a GET DPI command
        for dev_info in candidates:
            try:
                d = hid.device()
                d.open_path(dev_info["path"])
                self.handle = d
                self.info = dev_info

                result = self.get_dpi()
                if result and MIN_DPI <= result[0] <= MAX_DPI:
                    iface = dev_info.get("interface_number", "?")
                    return True, (f"{self.product_name} "
                                  f"(interface {iface})")
                d.close()
                self.handle = None
            except Exception:
                continue

        # Fallback — open whichever interface we can
        for dev_info in candidates:
            try:
                d = hid.device()
                d.open_path(dev_info["path"])
                self.handle = d
                self.info = dev_info
                iface = dev_info.get("interface_number", "?")
                return True, (f"{self.product_name} "
                              f"(interface {iface}, read unverified)")
            except Exception:
                continue

        return False, ("Could not open device.  Try:\n"
                       "• Close Razer Synapse\n"
                       "• Run this app as Administrator")

    def disconnect(self):
        if self.handle:
            try:
                self.handle.close()
            except Exception:
                pass
            self.handle = None
            self.info = None

    @property
    def connected(self) -> bool:
        return self.handle is not None

    # ── I/O ─────────────────────────────────────────────────────────────

    def _send_recv(self, report: bytes) -> bytes | None:
        """Send a feature report and read back the response."""
        if not self.handle:
            return None
        # Windows hidapi: first byte = report ID (0x00 for Razer)
        self.handle.send_feature_report(b"\x00" + report)
        time.sleep(0.08)   # give the MCU time to respond
        # Read back: report_id(1) + payload(90) = 91 bytes
        return bytes(self.handle.get_feature_report(0x00, RAZER_REPORT_LEN + 1))

    def get_dpi(self) -> tuple[int, int] | None:
        """Read current DPI from the mouse.  Returns (dpi_x, dpi_y)."""
        try:
            resp = self._send_recv(make_get_dpi())
            if resp is None or len(resp) < 14:
                return None
            # Check status byte — 0x02 = OK
            if resp[1] != 0x02:
                return None
            # Response layout (with 1‑byte report‑ID prefix from hidapi):
            #   [0]=rid  [1]=status  [2]=txn  [3..4]=remaining
            #   [5]=proto [6]=data_size [7]=cmd_class [8]=cmd_id
            #   [9]=args[0] (storage)  [10..11]=dpi_x  [12..13]=dpi_y
            dpi_x = (resp[10] << 8) | resp[11]
            dpi_y = (resp[12] << 8) | resp[13]
            return (dpi_x, dpi_y)
        except Exception:
            return None

    def set_dpi(self, dpi_x: int, dpi_y: int) -> bool:
        """Write a new DPI value.  Returns True on success."""
        try:
            resp = self._send_recv(make_set_dpi(dpi_x, dpi_y))
            if resp is not None and len(resp) > 1:
                return resp[1] == 0x02  # status OK
            return False
        except Exception:
            return False


# ── GUI ─────────────────────────────────────────────────────────────────────

# Color palette (Razer‑inspired dark theme)
BG_DARK     = "#0d0d0d"
BG_PANEL    = "#1a1a2e"
BG_CARD     = "#16213e"
GREEN       = "#00ff41"
GREEN_DIM   = "#00c853"
PINK        = "#e91e63"
WHITE       = "#f0f0f0"
GREY        = "#888888"
RED         = "#ff5252"
AMBER       = "#ffab00"


class App:
    """Tkinter GUI for the Razer DPI Changer."""

    def __init__(self):
        self.dev = RazerDevice()

        # ── root window ────────────────────────────────────────────────
        self.root = tk.Tk()
        self.root.title("Razer DeathAdder Essential — DPI Changer")
        self.root.geometry("540x640")
        self.root.minsize(480, 600)
        self.root.configure(bg=BG_DARK)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()

    # ── UI construction ─────────────────────────────────────────────────

    def _build_ui(self):
        root = self.root

        # ── Title bar ──────────────────────────────────────────────────
        hdr = tk.Frame(root, bg=BG_DARK)
        hdr.pack(fill="x", padx=24, pady=(18, 0))

        tk.Label(hdr, text="☠", font=("Segoe UI Emoji", 28),
                 fg=GREEN, bg=BG_DARK).pack(side="left")
        title_block = tk.Frame(hdr, bg=BG_DARK)
        title_block.pack(side="left", padx=12)
        tk.Label(title_block, text="DeathAdder Essential",
                 font=("Segoe UI", 18, "bold"),
                 fg=GREEN, bg=BG_DARK).pack(anchor="w")
        tk.Label(title_block, text="DPI Configuration Tool",
                 font=("Segoe UI", 10), fg=GREY, bg=BG_DARK).pack(anchor="w")

        # ── Connect button ─────────────────────────────────────────────
        conn_frame = tk.Frame(root, bg=BG_DARK)
        conn_frame.pack(pady=14)

        self.connect_btn = tk.Button(
            conn_frame, text="⚡  Connect Mouse",
            font=("Segoe UI", 11, "bold"),
            fg="white", bg=GREEN_DIM, activebackground=GREEN,
            relief="flat", padx=22, pady=7, cursor="hand2",
            command=self._on_connect,
        )
        self.connect_btn.pack()

        self.conn_label = tk.Label(
            root, text="⚪  Not connected",
            font=("Segoe UI", 9), fg=GREY, bg=BG_DARK,
        )
        self.conn_label.pack()

        # ── DPI readout card ───────────────────────────────────────────
        card = tk.Frame(root, bg=BG_CARD, highlightbackground="#0f3460",
                        highlightthickness=1)
        card.pack(padx=36, pady=(14, 8), fill="x")

        tk.Label(card, text="CURRENT DPI", font=("Segoe UI", 9, "bold"),
                 fg=GREY, bg=BG_CARD).pack(pady=(12, 0))

        self.dpi_readout = tk.Label(
            card, text="— — —",
            font=("Consolas", 44, "bold"), fg=GREEN, bg=BG_CARD,
        )
        self.dpi_readout.pack(pady=(2, 12))

        # ── Slider ─────────────────────────────────────────────────────
        slider_frame = tk.Frame(root, bg=BG_DARK)
        slider_frame.pack(padx=36, fill="x", pady=(6, 0))

        tk.Label(slider_frame, text="SET NEW DPI",
                 font=("Segoe UI", 9, "bold"),
                 fg=GREY, bg=BG_DARK).pack(anchor="w")

        self.dpi_var = tk.IntVar(value=800)

        self.slider = tk.Scale(
            slider_frame,
            from_=MIN_DPI, to=MAX_DPI, resolution=DPI_STEP,
            orient="horizontal", variable=self.dpi_var,
            font=("Consolas", 10), fg=GREEN, bg=BG_CARD,
            troughcolor="#0f3460", activebackground=GREEN,
            highlightthickness=0, bd=0, length=440,
            command=self._on_slider,
        )
        self.slider.pack(fill="x", pady=4)

        self.slider_val_label = tk.Label(
            slider_frame, text="800 DPI",
            font=("Consolas", 16, "bold"), fg=GREEN, bg=BG_DARK,
        )
        self.slider_val_label.pack(pady=(0, 4))

        # ── Presets ────────────────────────────────────────────────────
        preset_frame = tk.Frame(root, bg=BG_DARK)
        preset_frame.pack(padx=36, fill="x", pady=4)

        tk.Label(preset_frame, text="QUICK PRESETS",
                 font=("Segoe UI", 9, "bold"),
                 fg=GREY, bg=BG_DARK).pack(anchor="w", pady=(0, 4))

        btn_row = tk.Frame(preset_frame, bg=BG_DARK)
        btn_row.pack(fill="x")

        for dpi in (400, 800, 1200, 1600, 3200, 6400):
            b = tk.Button(
                btn_row, text=str(dpi),
                font=("Consolas", 11, "bold"),
                fg=GREEN, bg=BG_CARD, activeforeground="white",
                activebackground="#0f3460",
                relief="flat", padx=6, pady=5, cursor="hand2",
                command=lambda d=dpi: self._set_preset(d),
            )
            b.pack(side="left", expand=True, fill="x", padx=2)

        # ── Apply button ───────────────────────────────────────────────
        self.apply_btn = tk.Button(
            root, text="⚡  APPLY DPI",
            font=("Segoe UI", 14, "bold"),
            fg="white", bg=PINK, activebackground="#f44336",
            disabledforeground="#555",
            relief="flat", padx=36, pady=10, cursor="hand2",
            command=self._on_apply, state="disabled",
        )
        self.apply_btn.pack(pady=18)

        # ── Status bar ─────────────────────────────────────────────────
        self.status = tk.Label(
            root, text="Ready — click Connect to begin",
            font=("Segoe UI", 9), fg=GREY, bg="#111",
            anchor="w", padx=10, pady=4,
        )
        self.status.pack(side="bottom", fill="x")

    # ── callbacks ───────────────────────────────────────────────────────

    def _on_slider(self, _val):
        v = self.dpi_var.get()
        self.slider_val_label.config(text=f"{v} DPI")

    def _set_preset(self, dpi: int):
        self.dpi_var.set(dpi)
        self.slider_val_label.config(text=f"{dpi} DPI")

    def _on_connect(self):
        self.status.config(text="Searching for DeathAdder Essential…")
        self.root.update_idletasks()

        # Disconnect if already connected
        self.dev.disconnect()

        ok, msg = self.dev.connect()
        if ok:
            self.conn_label.config(text=f"🟢  {msg}", fg=GREEN)
            self.apply_btn.config(state="normal")
            self.connect_btn.config(text="🔄  Reconnect", bg="#455a64")

            result = self.dev.get_dpi()
            if result:
                dx, dy = result
                self.dpi_readout.config(text=str(dx))
                self.dpi_var.set(dx)
                self.slider_val_label.config(text=f"{dx} DPI")
                self.status.config(
                    text=f"✅ Connected — current DPI: {dx} × {dy}")
            else:
                self.dpi_readout.config(text="???")
                self.status.config(
                    text="Connected — could not read DPI")
        else:
            self.conn_label.config(text=f"🔴  Connection failed", fg=RED)
            self.status.config(text=msg)

    def _on_apply(self):
        dpi = self.dpi_var.get()
        self.status.config(text=f"Setting DPI to {dpi}…")
        self.root.update_idletasks()

        if self.dev.set_dpi(dpi, dpi):
            self.dpi_readout.config(text=str(dpi))
            self.status.config(text=f"✅  DPI set to {dpi}")

            # Verify by reading back
            time.sleep(0.1)
            result = self.dev.get_dpi()
            if result:
                dx, _ = result
                if dx == dpi:
                    self.status.config(
                        text=f"✅  DPI set to {dpi} — verified!")
                else:
                    self.status.config(
                        text=f"⚠️  Sent {dpi} but device reports {dx}")
                    self.dpi_readout.config(text=str(dx))
        else:
            self.status.config(
                text=f"❌  Failed to set DPI — try reconnecting")

    def _on_close(self):
        self.dev.disconnect()
        self.root.destroy()

    # ── main loop ───────────────────────────────────────────────────────

    def run(self):
        self.root.mainloop()


# ── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    App().run()
