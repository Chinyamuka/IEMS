"""
IEMS Image Upload Helper
========================

A single, reusable module for saving uploaded images to
disk under app/static/uploads/<subfolder>/.

Design goals
------------
1. One place for upload logic.
   Every feature that accepts an image (user profile,
   equipment photo, future category icon) calls the same
   two functions. There is no copy-paste drift.

2. Testable without Flask.
   The helper does not touch request, session, or g.
   The only Flask thing it reads is current_app.config,
   which is available inside any request or app context.

3. Safe by default.
   - Extension is validated against a config allowlist.
   - Content is verified with Pillow, not trusted from
     the browser's Content-Type header.
   - Filenames are random, not user-controlled.
   - Subfolder names are sanitized against traversal.

4. Predictable failure.
   Invalid uploads raise ImageUploadError. The route
   decides how to present the error to the user.
   "No file selected" is not an error — it returns None.
"""

# ---------------------------------------------------------
# STANDARD LIBRARY
# ---------------------------------------------------------

import os
import secrets
# ---------------------------------------------------------
# THIRD PARTY
# ---------------------------------------------------------
from PIL import Image, UnidentifiedImageError
# Pillow. Image.open inspects the file's magic bytes to
# determine a format. UnidentifiedImageError is the
# specific exception raised when the bytes are not a
# recognized image format.

from flask import current_app
# The active Flask application. We read
# current_app.config to get UPLOAD_FOLDER and
# ALLOWED_IMAGE_EXTENSIONS. current_app is a proxy
# that resolves to the running app inside a request
# or app context — so this module works in both
#  contexts and in tests using app.app_context().


# =========================================================
# CUSTOM EXCEPTION
# =========================================================

class ImageUploadError(Exception):
    """
    Raised when an uploaded file cannot be accepted.

    Reasons this is raised:
      - extension not in ALLOWED_IMAGE_EXTENSIONS
      - file contents are not a valid image
      - destination directory cannot be created
      - file cannot be written to disk
      - subfolder argument contains suspicious characters

    Why a custom exception and not flask.abort()?
      abort() raises HTTPException, which couples the
      helper to Flask's HTTP layer. That would make the
      function untestable without a request context.
      A plain exception lets the route decide what HTTP
      status and message to produce.
    """
    pass


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _extract_extension(filename: str) -> str:
    """
    Return the lowercase extension of a filename,
    without the leading dot.

    Examples
    --------
        "photo.JPG"       -> "jpg"
        "holiday.png"     -> "png"
        "no_extension"    -> ""
        "archive.tar.gz"  -> "gz"

    We deliberately extract only the last segment after
    the final dot, not everything after the first dot,
    because "report.final.pdf" must be treated as a
    PDF file, not as a file whose extension is
    "final.pdf".
    """

    # A filename with no dot has no extension.
    # Returning "" lets the caller reject it against
    # the allowlist without a special case.
    if "." not in filename:
        return ""

    # rpartition splits on the LAST occurrence of "."
    # and always returns a 3-tuple:
    #
    #     "archive.tar.gz".rpartition(".") -> ("archive.tar", ".", "gz")
    #     "no_extension".rpartition(".")   -> ("", "", "no_extension")
    #
    # This is safer than .split(".")[-1] because
    # split always returns at least one element and
    # forces the caller to reason about indexes.
    _, _, ext = filename.rpartition(".")

    # Lowercase so "PHOTO.JPG" and "photo.jpg" both work.
    return ext.lower()


def _generate_filename(extension: str) -> str:
    """
    Produce a random filename with the given extension.

    Uses secrets.token_hex(16), which yields 32 hex
    characters (128 bits of entropy). That is effectively
    collision-proof — you would need to generate billions
    of names per second for decades before a realistic
    chance of collision — but the caller still guards
    against it defensively.
    """

    # 32 random hex characters, e.g.:
    #   "a3f9c2e1f7b4d2c8e5a1b9f3d6c4e8a2"
    random_part = secrets.token_hex(16)

    # Preserve the extension so browsers and image
    # viewers still treat the file correctly.
    if extension:
        return f"{random_part}.{extension}"

    # If, somehow, no extension was extracted (should
    # not happen after validation), still return a
    # valid filename.
    return random_part


# =========================================================
# PUBLIC API — SAVE
# =========================================================

def save_image(file_storage, subfolder: str) -> str | None:
    """
    Validate and persist an uploaded image.

    Parameters
    ----------
    file_storage : werkzeug.datastructures.FileStorage
        The object produced by
        request.files.get("<field_name>").
        May be None if the form field was absent.
    subfolder : str
        Folder under UPLOAD_FOLDER where the file goes.
        Typically "users" or "equipment".

    Returns
    -------
    str | None
        The generated filename (no path) if a file was
        saved. None if no file was provided.

    Raises
    ------
    ImageUploadError
        If a file was provided but failed validation
        or could not be written.
    """

    # -----------------------------------------------------
    # STEP 1 — Was a file actually submitted?
    # -----------------------------------------------------
    #
    # When a browser submits a form with an empty file
    # input, it still sends the field — but the filename
    # is an empty string and the stream is empty.
    #
    # Treat this as "user did not change the image", not
    # as an error. Returning None lets the caller keep
    # the existing filename.
    #

    if file_storage is None or not file_storage.filename:
        return None

    # Remember the name for error messages and extension
    # extraction. Never trust this value for anything
    # security-relevant — it comes from the browser.
    original_name = file_storage.filename

    # -----------------------------------------------------
    # STEP 2 — Validate the extension.
    # -----------------------------------------------------
    #
    # This is the cheap first filter. It runs before we
    # touch Pillow, so obviously-wrong files are rejected
    # without the cost of parsing them.
    #

    extension = _extract_extension(original_name)

    # Read the allowlist from config. Using .get with a
    # default empty set means that a misconfigured app
    # rejects everything rather than accepting everything.
    allowed = current_app.config.get(
        "ALLOWED_IMAGE_EXTENSIONS",
        set(),
    )

    if extension not in allowed:
        raise ImageUploadError(
            "Unsupported file type. "
            "Allowed types: "
            + ", ".join(sorted(allowed))
        )

    # -----------------------------------------------------
    # STEP 3 — Validate the content.
    # -----------------------------------------------------
    #
    # The extension alone is trivially bypassed: rename
    # malware.exe to malware.jpg and the check passes.
    #
    # We therefore open the file with Pillow and let it
    # decide. Pillow reads the file's magic bytes and
    # internal structure. If the file is not a real
    # image, Image.open or verify raises.
    #
    # Important: verify() consumes the stream. We must
    # seek(0) afterwards so save() writes the whole file,
    # not just the tail end of it.
    #

    try:
        # Rewind first — some earlier middleware (or a
        # future route) may have partially read the stream.
        file_storage.stream.seek(0)

        # Image.open does not decode pixels; it just
        # parses the header. verify() then checks the
        # file's internal integrity.
        with Image.open(file_storage.stream) as img:
            img.verify()

        # Rewind again so the stream is at byte 0 for save().
        file_storage.stream.seek(0)

    except (UnidentifiedImageError, OSError, ValueError):
        # UnidentifiedImageError — not a recognized format.
        # OSError                — truncated or unreadable.
        # ValueError             — malformed header.
        raise ImageUploadError(
            "The file is not a valid image."
        )

    # -----------------------------------------------------
    # STEP 4 — Resolve the destination directory.
    # -----------------------------------------------------
    #
    # The subfolder comes from the calling route, so
    # today it is always a trusted constant. But we guard
    # anyway: if a future caller ever forwards user input
    # here, "../config" must not escape UPLOAD_FOLDER.
    #

    upload_root = current_app.config["UPLOAD_FOLDER"]

    if "/" in subfolder or "\\" in subfolder or ".." in subfolder:
        raise ImageUploadError(
            "Invalid upload destination."
        )

    # os.path.join uses the correct separator for the
    # platform. On Linux it produces "a/b"; on Windows
    # it would produce "a\\b".
    destination_dir = os.path.join(upload_root, subfolder)

    # The directories are created in the config commit,
    # but we re-create defensively in case the app is
    # deployed onto a clean machine whose upload folder
    # was never seeded.
    #
    # exist_ok=True means "do not raise if it already
    # exists" — otherwise we would have to wrap this in
    # a try/except FileExistsError.
    os.makedirs(destination_dir, exist_ok=True)

    # -----------------------------------------------------
    # STEP 5 — Pick a filename that does not collide.
    # -----------------------------------------------------
    #
    # secrets already makes collisions vanishingly rare,
    # but a filesystem can only have one file per name.
    # This loop is effectively free and makes the whole
    # operation airtight.
    #

    filename = _generate_filename(extension)
    full_path = os.path.join(destination_dir, filename)

    while os.path.exists(full_path):
        filename = _generate_filename(extension)
        full_path = os.path.join(destination_dir, filename)

    # -----------------------------------------------------
    # STEP 6 — Write the file.
    # -----------------------------------------------------
    #
    # file_storage.save writes the multipart stream to
    # the target path. The stream is at byte 0 from
    # Step 3, so the whole file is copied.
    #

    try:
        file_storage.save(full_path)
    except OSError:
        # Disk full, permissions, read-only mount, etc.
        raise ImageUploadError(
            "The image could not be saved. "
            "Please try again."
        )

    # -----------------------------------------------------
    # STEP 7 — Return only the filename.
    # -----------------------------------------------------
    #
    # The database stores "<random>.jpg", not the full
    # path. Templates then build the URL with
    #
    #     url_for('static',
    #             filename='uploads/users/' ~ filename)
    #
    # This means the physical location can change later
    # (e.g. move to object storage) without touching any
    # row in the database.
    #

    return filename


# =========================================================
# PUBLIC API — DELETE
# =========================================================

def delete_image(filename: str, subfolder: str) -> bool:
    """
    Delete a previously uploaded image from disk.

    Returns
    -------
    bool
        True  — file existed and was removed.
        False — file did not exist, or could not be
                removed (permissions, locked by another
                process, etc.).

    Why this does not raise
    -----------------------
    This function is called from routes that are
    replacing an old image. If the old file has already
    been removed externally, or the disk is read-only,
    the user-facing operation should still succeed —
    the visible outcome (a new image is stored) is
    unaffected.
    """

    # A None or empty filename means "there was no
    # previous image". Nothing to delete.
    if not filename:
        return False

    upload_root = current_app.config["UPLOAD_FOLDER"]

    # Same traversal guard as save_image. Refuse to
    # build a path that could leave the upload root.
    if "/" in subfolder or "\\" in subfolder or ".." in subfolder:
        return False

    full_path = os.path.join(
        upload_root,
        subfolder,
        filename,
    )

    try:
        os.remove(full_path)
        return True
    except FileNotFoundError:
        # The file was already gone. Report False so the
        # caller can log if it cares, but do not raise.
        return False
    except OSError:
        # Permissions, mounted read-only, in use, etc.
        # Non-fatal: the new upload still succeeded.
        return False
