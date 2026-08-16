"""
tm_t20.py
---------

Python ESC/POS controller for the ORIGINAL Epson TM-T20.

Communication:
    Epson Send Data Tool (Senddat.exe)
    USB Printer Class

Example:
    printer = TMT20(
        senddat=r"C:\Epson\Senddat.exe",
        usb_port="USBPRN0"
    )

    printer.init()
    printer.align("center")
    printer.bold(True)
    printer.size(2, 2)
    printer.line("HELLO")
    printer.bold(False)
    printer.size(1, 1)
    printer.feed(3)
    printer.cut()
    printer.send()

IMPORTANT:
    The USB endpoint is NOT necessarily "USBPRN0".
    Check the Epson Send Data Tool configuration on your PC.
"""

from __future__ import annotations

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Iterable, Optional


class TMT20Error(Exception):
    pass


class TMT20:

    # ---------------------------------------------------------
    # CONSTRUCTOR
    # ---------------------------------------------------------

    def __init__(
        self,
        senddat: str = r"C:\Epson\Senddat.exe",
        usb_port: str = "USBPRN0",
        encoding: str = "cp852",
        keep_script: bool = False,
    ):
        self.senddat = Path(senddat)
        self.usb_port = usb_port
        self.encoding = encoding
        self.keep_script = keep_script

        # Locally queued ESC/POS data
        self.data = bytearray()

    # =========================================================
    # LOW LEVEL
    # =========================================================

    def raw(self, data: bytes | bytearray | Iterable[int]):
        """
        Add completely raw ESC/POS bytes.

        Example:
            printer.raw(b"Hello")
            printer.raw([0x1B, 0x40])
        """

        if isinstance(data, (bytes, bytearray)):
            self.data.extend(data)
        else:
            self.data.extend(int(x) & 0xFF for x in data)

        return self

    def byte(self, value: int):
        self.data.append(value & 0xFF)
        return self

    def bytes(self, *values: int):
        self.data.extend(v & 0xFF for v in values)
        return self

    # =========================================================
    # LOCAL BUFFER
    # =========================================================

    def clear(self):
        """
        Clear the Python-side output buffer.

        This does NOT send anything to the printer.
        """

        self.data.clear()
        return self

    def queued_size(self) -> int:
        """Return number of bytes currently queued."""
        return len(self.data)

    # =========================================================
    # PRINTER INITIALIZATION
    # =========================================================

    def init(self):
        """
        ESC @

        Initialize printer.
        """

        return self.bytes(0x1B, 0x40)

    # =========================================================
    # BASIC PRINTING
    # =========================================================

    def text(self, text: str):
        """Add encoded text."""

        self.data.extend(text.encode(self.encoding))
        return self

    def line(self, text: str = ""):
        """Print text followed by LF."""

        self.text(text)
        self.lf()

        return self

    def lf(self):
        """LF - Print and line feed."""

        return self.byte(0x0A)

    def cr(self):
        """CR - Print and carriage return."""

        return self.byte(0x0D)

    def tab(self):
        """HT - horizontal tab."""

        return self.byte(0x09)

    def ff(self):
        """
        FF.

        In page mode this prints and returns to standard mode.
        """

        return self.byte(0x0C)

    # =========================================================
    # FEEDING
    # =========================================================

    def feed(self, lines: int = 1):
        """
        ESC d n

        Print and feed n lines.
        """

        if not 0 <= lines <= 255:
            raise ValueError("lines must be 0..255")

        return self.bytes(
            0x1B, 0x64, lines
        )

    def feed_dots(self, dots: int):
        """
        ESC J n

        Print and feed n dots.
        """

        if not 0 <= dots <= 255:
            raise ValueError("dots must be 0..255")

        return self.bytes(
            0x1B, 0x4A, dots
        )

    # =========================================================
    # ALIGNMENT
    # =========================================================

    def align(self, alignment: str):
        """
        ESC a n

        left
        center
        right
        """

        values = {
            "left": 0,
            "center": 1,
            "right": 2,
        }

        alignment = alignment.lower()

        if alignment not in values:
            raise ValueError(
                "alignment must be: left, center or right"
            )

        return self.bytes(
            0x1B,
            0x61,
            values[alignment]
        )

    # =========================================================
    # TEXT STYLE
    # =========================================================

    def bold(self, enabled: bool = True):
        """
        ESC E n

        Emphasized mode.
        """

        return self.bytes(
            0x1B,
            0x45,
            1 if enabled else 0
        )

    def double_strike(self, enabled: bool = True):
        """
        ESC G n
        """

        return self.bytes(
            0x1B,
            0x47,
            1 if enabled else 0
        )

    def underline(self, enabled: bool = True, thickness: int = 1):
        """
        ESC - n

        thickness:
            0 = off
            1 = 1-dot
            2 = 2-dot
        """

        if not enabled:
            thickness = 0

        if thickness not in (0, 1, 2):
            raise ValueError("thickness must be 0, 1 or 2")

        return self.bytes(
            0x1B,
            0x2D,
            thickness
        )

    def font(self, font: int = 0):
        """
        ESC M n

        0 = Font A
        1 = Font B
        """

        if font not in (0, 1):
            raise ValueError("font must be 0 or 1")

        return self.bytes(
            0x1B,
            0x4D,
            font
        )

    def size(self, width: int = 1, height: int = 1):
        """
        GS ! n

        Width/height:
            1..8
        """

        if not 1 <= width <= 8:
            raise ValueError("width must be 1..8")

        if not 1 <= height <= 8:
            raise ValueError("height must be 1..8")

        n = ((width - 1) << 4) | (height - 1)

        return self.bytes(
            0x1D,
            0x21,
            n
        )

    def invert(self, enabled: bool = True):
        """
        GS B n

        White/black reverse mode.
        """

        return self.bytes(
            0x1D,
            0x42,
            1 if enabled else 0
        )

    def upside_down(self, enabled: bool = True):
        """
        ESC { n
        """

        return self.bytes(
            0x1B,
            0x7B,
            1 if enabled else 0
        )

    def rotate(self, enabled: bool = True):
        """
        ESC V n

        90 degree rotation.
        """

        return self.bytes(
            0x1B,
            0x56,
            1 if enabled else 0
        )

    def normal(self):
        """Return to normal text formatting."""

        self.bold(False)
        self.double_strike(False)
        self.underline(False)
        self.invert(False)
        self.upside_down(False)
        self.rotate(False)
        self.font(0)
        self.size(1, 1)

        return self

    # =========================================================
    # CHARACTER TABLE / ENCODING
    # =========================================================

    def codepage(self, table: int):
        """
        ESC t n

        Select printer character code table.
        """

        if not 0 <= table <= 255:
            raise ValueError("table must be 0..255")

        return self.bytes(
            0x1B,
            0x74,
            table
        )

    def international(self, country: int):
        """
        ESC R n
        """

        return self.bytes(
            0x1B,
            0x52,
            country
        )

    # =========================================================
    # CHARACTER SPACING
    # =========================================================

    def right_spacing(self, dots: int):
        """
        ESC SP n
        """

        if not 0 <= dots <= 255:
            raise ValueError("dots must be 0..255")

        return self.bytes(
            0x1B,
            0x20,
            dots
        )

    # =========================================================
    # LINE SPACING
    # =========================================================

    def line_spacing(self, dots: int):
        """
        ESC 3 n
        """

        if not 0 <= dots <= 255:
            raise ValueError("dots must be 0..255")

        return self.bytes(
            0x1B,
            0x33,
            dots
        )

    def default_line_spacing(self):
        """
        ESC 2
        """

        return self.bytes(
            0x1B,
            0x32
        )

    # =========================================================
    # HORIZONTAL POSITION
    # =========================================================

    def absolute(self, position: int):
        """
        ESC $ nL nH

        Absolute print position.
        """

        if not 0 <= position <= 65535:
            raise ValueError("position must be 0..65535")

        return self.bytes(
            0x1B,
            0x24,
            position & 0xFF,
            (position >> 8) & 0xFF
        )

    def relative(self, position: int):
        """
        ESC \\ nL nH

        Relative horizontal position.
        """

        if not -32768 <= position <= 32767:
            raise ValueError(
                "position must be -32768..32767"
            )

        if position < 0:
            position += 65536

        return self.bytes(
            0x1B,
            0x5C,
            position & 0xFF,
            (position >> 8) & 0xFF
        )

    def tabs(self, positions: Iterable[int]):
        """
        ESC D ...

        Define horizontal tab positions.
        """

        positions = list(positions)

        self.bytes(0x1B, 0x44)

        for p in positions:
            if not 1 <= p <= 255:
                raise ValueError(
                    "tab positions must be 1..255"
                )

            self.byte(p)

        self.byte(0)

        return self

    # =========================================================
    # PAGE MODE
    # =========================================================

    def page_mode(self):
        """ESC L"""

        return self.bytes(
            0x1B,
            0x4C
        )

    def standard_mode(self):
        """ESC S"""

        return self.bytes(
            0x1B,
            0x53
        )

    def page_print(self):
        """ESC FF"""

        return self.bytes(
            0x1B,
            0x0C
        )

    def page_cancel(self):
        """CAN"""

        return self.byte(0x18)

    # =========================================================
    # BIT IMAGE
    # =========================================================

    def bit_image(
        self,
        data: bytes,
        width_bytes: int,
        mode: int = 0,
    ):
        """
        ESC * m nL nH

        mode:
            0  = 8-dot single density
            1  = 8-dot double density
            32 = 24-dot single density
            33 = 24-dot double density
        """

        if mode not in (0, 1, 32, 33):
            raise ValueError(
                "Invalid ESC * image mode"
            )

        if width_bytes < 1:
            raise ValueError("width_bytes must be > 0")

        self.bytes(
            0x1B,
            0x2A,
            mode,
            width_bytes & 0xFF,
            (width_bytes >> 8) & 0xFF,
        )

        self.raw(data)

        return self

    # =========================================================
    # BARCODE
    # =========================================================

    def barcode_height(self, height: int):
        """
        GS h n
        """

        if not 1 <= height <= 255:
            raise ValueError("height must be 1..255")

        return self.bytes(
            0x1D,
            0x68,
            height
        )

    def barcode_width(self, width: int):
        """
        GS w n

        2..6
        """

        if not 2 <= width <= 6:
            raise ValueError("width must be 2..6")

        return self.bytes(
            0x1D,
            0x77,
            width
        )

    def barcode_text(
        self,
        position: int = 2,
    ):
        """
        GS H n

        0 = none
        1 = above
        2 = below
        3 = above and below
        """

        if position not in (0, 1, 2, 3):
            raise ValueError("invalid HRI position")

        return self.bytes(
            0x1D,
            0x48,
            position
        )

    def barcode_font(self, font: int = 0):
        """
        GS f n
        """

        if font not in (0, 1):
            raise ValueError("font must be 0 or 1")

        return self.bytes(
            0x1D,
            0x66,
            font
        )

    def barcode(
        self,
        barcode_type: int,
        data: str | bytes,
    ):
        """
        GS k m ...

        Raw ESC/POS barcode interface.

        barcode_type is the Epson ESC/POS type number.
        """

        if isinstance(data, str):
            data = data.encode("ascii")

        self.bytes(
            0x1D,
            0x6B,
            barcode_type
        )

        # Types 0..6 use NUL terminated data.
        if barcode_type <= 6:
            self.raw(data)
            self.byte(0)

        else:
            if len(data) > 255:
                raise ValueError(
                    "barcode data too long"
                )

            self.byte(len(data))
            self.raw(data)

        return self

    # =========================================================
    # QR CODE
    # =========================================================

    def qr_size(self, size: int = 4):
        """
        GS ( k

        QR module size.
        """

        if not 1 <= size <= 16:
            raise ValueError("QR size must be 1..16")

        return self.bytes(
            0x1D,
            0x28,
            0x6B,
            0x03,
            0x00,
            0x31,
            0x43,
            size
        )

    def qr_error_correction(self, level: int = 48):
        """
        QR error correction.

        Epson values:
            48 = L
            49 = M
            50 = Q
            51 = H
        """

        if level not in (48, 49, 50, 51):
            raise ValueError(
                "QR correction must be 48..51"
            )

        return self.bytes(
            0x1D,
            0x28,
            0x6B,
            0x03,
            0x00,
            0x31,
            0x45,
            level
        )

    def qr_print(self, data: str):
        """
        Store and print a QR code.
        """

        payload = data.encode(self.encoding)

        length = len(payload) + 3

        pL = length & 0xFF
        pH = (length >> 8) & 0xFF

        # Store QR data
        self.bytes(
            0x1D,
            0x28,
            0x6B,
            pL,
            pH,
            0x31,
            0x50,
            0x30
        )

        self.raw(payload)

        # Print QR
        self.bytes(
            0x1D,
            0x28,
            0x6B,
            0x03,
            0x00,
            0x31,
            0x51,
            0x30
        )

        return self

    def qrcode(
        self,
        data: str,
        size: int = 4,
        error_correction: str = "M",
    ):
        """
        Convenience QR function.
        """

        levels = {
            "L": 48,
            "M": 49,
            "Q": 50,
            "H": 51,
        }

        error_correction = error_correction.upper()

        if error_correction not in levels:
            raise ValueError(
                "error_correction must be L, M, Q or H"
            )

        self.qr_size(size)
        self.qr_error_correction(
            levels[error_correction]
        )
        self.qr_print(data)

        return self

    # =========================================================
    # CUTTER
    # =========================================================

    def cut(self, partial: bool = False):
        """
        GS V

        partial=False:
            full cut

        partial=True:
            partial cut
        """

        return self.bytes(
            0x1D,
            0x56,
            1 if partial else 0
        )

    # =========================================================
    # CASH DRAWER
    # =========================================================

    def drawer(
        self,
        pin: int = 0,
        duration: int = 4,
    ):
        """
        DLE DC4 fn=1

        pin:
            0 = drawer pin 2
            1 = drawer pin 5

        duration:
            1..8

        ON = duration * 100 ms
        OFF = duration * 100 ms
        """

        if pin not in (0, 1):
            raise ValueError("pin must be 0 or 1")

        if not 1 <= duration <= 8:
            raise ValueError(
                "duration must be 1..8"
            )

        return self.bytes(
            0x10,
            0x14,
            0x01,
            pin,
            duration
        )

    # =========================================================
    # BUZZER
    # =========================================================

    def beep(self):
        """
        DLE DC4 fn=3

        Real-time buzzer command.
        """

        return self.bytes(
            0x10,
            0x14,
            0x03
        )

    # =========================================================
    # PANEL BUTTON
    # =========================================================

    def panel_button(self, enabled: bool = True):
        """
        ESC c 5 n

        Enable/disable FEED button.
        """

        return self.bytes(
            0x1B,
            0x63,
            0x35,
            1 if enabled else 0
        )

    # =========================================================
    # PERIPHERAL DEVICE
    # =========================================================

    def peripheral(self, device: int = 1):
        """
        ESC = n

        device:
            0 = disable
            1 = printer
        """

        return self.bytes(
            0x1B,
            0x3D,
            device
        )

    # =========================================================
    # USER DEFINED CHARACTERS
    # =========================================================

    def cancel_user_characters(self):
        """
        ESC ?
        """

        return self.bytes(
            0x1B,
            0x3F
        )

    # =========================================================
    # STATUS
    # =========================================================

    def status(self, status_type: int = 1):
        """
        DLE EOT n

        Adds a real-time status request.

        IMPORTANT:
            This requires reading the printer response.
            Send Data Tool is primarily a send utility, so
            this method is useful for generating the command,
            but it does not itself return the USB response.
        """

        if not 1 <= status_type <= 4:
            raise ValueError(
                "status_type must be 1..4"
            )

        return self.bytes(
            0x10,
            0x04,
            status_type
        )

    def realtime_request(self, n: int):
        """
        DLE ENQ n
        """

        return self.bytes(
            0x10,
            0x05,
            n
        )

    # =========================================================
    # PRINTER BUFFER
    # =========================================================

    def clear_printer_buffer(self):
        """
        DLE DC4 fn=8

        ORIGINAL TM-T20:

            10 14 08 01 03 14 01 06 02 08

        Clears:
            - receive buffer
            - print buffer

        Epson specifies that this is a REAL-TIME command and
        that subsequent data should not be sent until the
        printer has returned its Clear response.

        Because Send Data Tool is not a bidirectional API,
        this method sends the command as a separate job.
        """

        # Make sure this command is not mixed into a large
        # print job.
        old_data = self.data
        self.data = bytearray()

        self.bytes(
            0x10,
            0x14,
            0x08,
            0x01,
            0x03,
            0x14,
            0x01,
            0x06,
            0x02,
            0x08,
        )

        try:
            self.send()

        finally:
            self.data = old_data

        return self

    # =========================================================
    # MECHANISM CONTROL
    # =========================================================

    def home(self):
        """
        ESC <

        Return print head to home position.
        """

        return self.bytes(
            0x1B,
            0x3C
        )

    # =========================================================
    # RAW COMMAND HELPERS
    # =========================================================

    def esc(self, command: int, *args: int):
        """
        Generic ESC command.

        Example:
            printer.esc(0x45, 1)
        """

        return self.bytes(
            0x1B,
            command,
            *args
        )

    def gs(self, command: int, *args: int):
        """
        Generic GS command.

        Example:
            printer.gs(0x21, 0x11)
        """

        return self.bytes(
            0x1D,
            command,
            *args
        )

    def dle(self, command: int, *args: int):
        """
        Generic DLE command.
        """

        return self.bytes(
            0x10,
            command,
            *args
        )

    # =========================================================
    # SEND DATA TOOL SCRIPT
    # =========================================================

    def make_script(self) -> str:
        """
        Convert queued binary data into Epson Send Data Tool
        script syntax.

        Decimal bytes are used because Send Data Tool explicitly
        supports decimal byte data.
        """

        if not self.data:
            return ""

        output = []

        for b in self.data:
            output.append(str(b))

        return " ".join(output)

    def save_script(self, filename: str):
        """
        Save Send Data Tool script.
        """

        Path(filename).write_text(
            self.make_script(),
            encoding="ascii"
        )

        return self

    # =========================================================
    # SEND
    # =========================================================

    def send(self):
        """
        Send current data through Senddat.exe.
        """

        if not self.senddat.exists():
            raise FileNotFoundError(
                f"Send Data Tool not found:\n"
                f"{self.senddat}"
            )

        if not self.data:
            raise TMT20Error(
                "Nothing to send."
            )

        script = self.make_script()

        temp_name = None

        if self.keep_script:

            filename = (
                Path.cwd() /
                "tm_t20_senddat.txt"
            )

            filename.write_text(
                script,
                encoding="ascii"
            )

        else:

            fd, temp_name = tempfile.mkstemp(
                suffix=".txt",
                prefix="tm_t20_"
            )

            os.close(fd)

            filename = Path(temp_name)

            filename.write_text(
                script,
                encoding="ascii"
            )

        try:

            result = subprocess.run(
                [
                    str(self.senddat),
                    str(filename),
                    self.usb_port,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:

                raise TMT20Error(
                    "Send Data Tool failed.\n\n"
                    f"Return code: {result.returncode}\n"
                    f"STDOUT:\n{result.stdout}\n"
                    f"STDERR:\n{result.stderr}"
                )

        finally:

            if not self.keep_script:
                try:
                    filename.unlink()
                except OSError:
                    pass

        return self

    # =========================================================
    # SEND + CLEAR LOCAL BUFFER
    # =========================================================

    def print(self):
        """
        Send the current job and then clear the Python buffer.
        """

        self.send()
        self.clear()

        return self


# =============================================================
# EXAMPLE
# =============================================================

if __name__ == "__main__":

    printer = TMT20(
        senddat=r"./senddat.exe",
        usb_port="USBPRN0",
        encoding="cp852",
        keep_script=False,
    )

    # ---------------------------------------------------------
    # TEST RECEIPT
    # ---------------------------------------------------------

    printer.init()

    printer.align("center")

    printer.bold(True)
    printer.size(2, 2)

    printer.line("EPSON TM-T20")

    printer.size(1, 1)
    printer.bold(False)

    printer.line("Python ESC/POS test")
    printer.line("")

    printer.align("left")

    printer.line("--------------------------------")
    printer.line("Item                    Price")
    printer.line("--------------------------------")

    printer.line("Coffee                   2.50")
    printer.line("Sandwich                 5.90")
    printer.line("Water                    1.20")

    printer.line("--------------------------------")

    printer.bold(True)
    printer.line("TOTAL                    9.60")
    printer.bold(False)

    printer.line("")
    printer.align("center")

    printer.qrcode(
        "https://example.com",
        size=5,
        error_correction="M",
    )

    printer.line("")
    printer.feed(3)

    printer.cut()

    printer.print()