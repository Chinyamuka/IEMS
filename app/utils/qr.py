"""
IEMS QR Code Generator

Generates a QR PNG from an arbitrary string (typically
a URL) and returns the raw PNG bytes. Nothing is written
to disk — callers stream the bytes straight to the browser.
"""

import io

import qrcode
from qrcode.constants import ERROR_CORRECT_M


def generate_qr_png(data: str, box_size: int = 10, border: int = 2) -> bytes:
    """Render the given string as a QR PNG and return the bytes."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer.getvalue()
