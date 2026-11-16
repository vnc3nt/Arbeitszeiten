import os
import io
import base64
from PIL import Image
from flask import url_for
from models import db, users

PROFILE_IMAGE_DEFAULT = "img/icons/512x512-profile.webp"
PROFILE_IMAGE_FOLDER = os.path.join("uploads", "profile_images")
PROFILE_IMAGE_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
PROFILE_IMAGE_MAX_SIZE = 2 * 1024 * 1024

# ABS_FOLDER: berechne relativ zum Modul, kein app.static_folder nötig
_HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE_IMAGE_ABS_FOLDER = os.path.join(_HERE, '..', 'static', PROFILE_IMAGE_FOLDER)


def _get_static_folder():
    from flask import current_app
    return current_app.static_folder


def allowed_profile_image(filename: str) -> bool:
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in PROFILE_IMAGE_ALLOWED_EXTENSIONS


def get_profile_image_url() -> str:
    from utils.session_helpers import get_current_user
    user = get_current_user()
    if user and user.profile_image:
        if user.profile_image.startswith("data:image/"):
            return user.profile_image

        # Fallback für eventuell noch vorhandene lokale Dateien aus früheren Uploads
        absolute_path = os.path.join(_get_static_folder(), user.profile_image)
        if os.path.exists(absolute_path):
            return url_for("static", filename=user.profile_image)

    return url_for("static", filename=PROFILE_IMAGE_DEFAULT)


def remove_profile_image_file(profile_image_path):
    if not profile_image_path or profile_image_path.startswith("data:image/"):
        return

    base_dir = os.path.realpath(PROFILE_IMAGE_ABS_FOLDER)
    absolute_path = os.path.realpath(os.path.join(_get_static_folder(), profile_image_path))
    if os.path.commonpath([base_dir, absolute_path]) == base_dir and os.path.exists(absolute_path):
        try:
            os.remove(absolute_path)
        except OSError:
            pass


def save_profile_image(uploaded_file, user):
    if uploaded_file is None or not uploaded_file.filename:
        return "Bitte eine Bilddatei auswählen"

    if not allowed_profile_image(uploaded_file.filename):
        return "Nur PNG, JPG oder WEBP sind erlaubt"

    try:
        # Prüft, ob es sich wirklich um eine valide Bilddatei handelt
        img = Image.open(uploaded_file.stream)
        img.verify()
        uploaded_file.stream.seek(0)
        img = Image.open(uploaded_file.stream)
    except Exception:
        return "Ungültige oder beschädigte Bilddatei"

    # Bild auf max. 384x384 begrenzen (optimale Schärfe für Retina-Displays bei minimaler Dateigröße)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    img.thumbnail((384, 384))

    # Als WebP komprimieren und als persistente Data-URL direkt in der PostgreSQL-DB ablegen
    try:
        buffer = io.BytesIO()
        img.save(buffer, format="WEBP", quality=82, method=6)
        encoded_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
        data_url = f"data:image/webp;base64,{encoded_data}"

        previous_profile_image = user.profile_image
        user.profile_image = data_url
        db.session.commit()
    except Exception:
        db.session.rollback()
        return "Profilbild konnte nicht in der Datenbank gespeichert werden"

    # Wenn zuvor eine lokale Datei auf der Festplatte lag, diese säubern
    if previous_profile_image and not previous_profile_image.startswith("data:image/"):
        remove_profile_image_file(previous_profile_image)

    return None


def reset_profile_image(user):
    previous_profile_image = user.profile_image
    user.profile_image = None

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return "Profilbild konnte nicht zurückgesetzt werden"

    if previous_profile_image and not previous_profile_image.startswith("data:image/"):
        remove_profile_image_file(previous_profile_image)
    return None
