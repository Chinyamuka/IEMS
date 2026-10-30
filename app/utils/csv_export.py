"""
CSV export helper.

One function to turn a list of dicts (or rows) into a
CSV HTTP response. Used by:
    GET /equipment/export.csv
    GET /users/export.csv
    GET /activity/export.csv

The output is UTF-8 with a BOM (byte-order mark) so
Excel opens it correctly without the "you might be
opening a file from an untrusted source" warning on
legacy Excel. UTF-8-BOM is what enterprise tools expect.
"""

import csv
import io
from datetime import datetime

from flask import Response


def csv_response(
    rows: list[dict],
    filename_prefix: str = "iems-export",
    extra_headers: dict | None = None,
) -> Response:
    """
    Build a CSV Response from a list of dicts.

    Parameters
    ----------
    rows : list[dict]
        One dict per row. Keys are used as the header row
        (first row's keys, in insertion order).
    filename_prefix : str
        Prepended to the timestamp for the filename.
    extra_headers : dict | None
        Additional HTTP headers to set on the response
        (e.g. cache-control).

    Returns
    -------
    flask.Response
        CSV download with Content-Disposition attachment.
    """
    if not rows:
        body = io.StringIO()
        body.write("(no rows)\n")
        payload = body.getvalue().encode("utf-8-sig")

        filename = (
            f"{filename_prefix}-"
            f"{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.csv"
        )
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        if extra_headers:
            headers.update(extra_headers)
        return Response(payload, mimetype="text/csv", headers=headers)

    headers_row = list(rows[0].keys())

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=headers_row,
        extrasaction="ignore",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writeheader()
    for row in rows:
        clean = {}
        for k, v in row.items():
            if v is None:
                clean[k] = ""
            elif isinstance(v, datetime):
                clean[k] = v.strftime("%Y-%m-%d %H:%M:%S")
            elif hasattr(v, "isoformat"):
                clean[k] = v.isoformat()
            else:
                clean[k] = v
        writer.writerow(clean)

    payload = buffer.getvalue().encode("utf-8-sig")

    filename = (
        f"{filename_prefix}-"
        f"{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.csv"
    )
    http_headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Cache-Control": "no-store",
    }
    if extra_headers:
        http_headers.update(extra_headers)

    return Response(payload, mimetype="text/csv", headers=http_headers)
