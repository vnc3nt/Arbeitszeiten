import re
import json
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Dict, Tuple, List, Any
from urllib.parse import urlparse
from flask import Blueprint, render_template, redirect, request, session, url_for, jsonify, send_file
from sqlalchemy import func
from werkzeug.utils import secure_filename
from models import db, users, profiles, data, category
from constants import USERID, PROFILEID
from extensions import csrf
from login import validTokenChecker
from translations import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, get_month_name
from export_utils import generate_excel_export, generate_pdf_export
from login import change_password, change_username, delete_account
from utils.session_helpers import (
    get_username, get_active_profile_name, get_profile_list, get_all_profile_list,
    get_current_language, get_current_theme, SUPPORTED_THEMES,
)
from utils.profile_images import get_profile_image_url, save_profile_image, reset_profile_image
from extensions import limiter

profile_bp = Blueprint('profile', __name__)


def get_safe_redirect_url(fallback_endpoint: str = "home.home") -> str:
    referrer = request.referrer
    if not referrer:
        return url_for(fallback_endpoint)
    parsed = urlparse(referrer)
    if (not parsed.netloc or parsed.netloc == request.host) and parsed.scheme in ("", "http", "https"):
        return referrer
    return url_for(fallback_endpoint)


def get_current_user():
    return db.session.query(users).filter(users.id == session.get(USERID)).first()


@profile_bp.route('/profile', methods=["GET", "POST"])
@limiter.limit("20 per minute")
@validTokenChecker
def profile():
    profile_message = request.args.get("profile_message")
    if request.method == "POST":
        action = request.form.get("action")
        if action == "change-username":
            result = change_username(request.form.get("new_username"))

        elif action == "change-profile-picture":
            user = get_current_user()
            result = save_profile_image(request.files.get("profile_image"), user) if user else "Benutzer nicht gefunden"
            if result is None:
                return redirect(url_for("profile.profile"))

        elif action == "reset-profile-picture":
            user = get_current_user()
            if user:
                result = reset_profile_image(user)
                if result is None:
                    return redirect(url_for("profile.profile"))
            else:
                result = "Benutzer nicht gefunden"

        elif action == "delete-account":
            result = delete_account(request.form.get("password"))
            if result is None:
                return redirect("/login")

        elif action == "change-password":
            current_pw = request.form.get("current-password")
            new_pw = request.form.get("new-password")
            new_pw_confirm = request.form.get("new-password-confirmation")
            result = change_password(current_pw, new_pw, new_pw_confirm)
            if result is None:
                return redirect("/login")

        else:
            result = "Unbekannte Aktion"

        profile_message = result
    return render_template('profile.html', user_id=session.get(USERID), get_username=get_username,
                           get_active_profile_name=get_active_profile_name,
                           profile_image_url=get_profile_image_url(), profile_message=profile_message,
                           profiles=get_profile_list(), active_profile_id=session.get(PROFILEID),
                           all_profiles=get_all_profile_list())


@profile_bp.route('/profiles/manage', methods=['POST'])
@validTokenChecker
def manage_profile():
    wants_json = request.headers.get("X-Requested-With") == "fetch" or request.is_json
    action = request.form.get('profile_action')

    if action == 'reorder':
        order_raw = request.form.get('order') or request.form.getlist('order[]')
        if isinstance(order_raw, str):
            try:
                order_list = json.loads(order_raw)
            except Exception:
                order_list = [x.strip() for x in order_raw.split(',') if x.strip()]
        elif isinstance(order_raw, list):
            order_list = order_raw
        else:
            order_list = []

        if order_list:
            for idx, p_id in enumerate(order_list):
                try:
                    p_id_int = int(p_id)
                    db.session.query(profiles).filter_by(
                        id=p_id_int, userid=session.get(USERID)
                    ).update({"position": idx})
                except (ValueError, TypeError):
                    continue
            db.session.commit()

        if wants_json:
            return jsonify(success=True, message="Reihenfolge gespeichert")
        return redirect(url_for('profile.profile', profile_message="Reihenfolge gespeichert"))

    if action == 'create':
        existing_names = {p.name for p in db.session.query(profiles.name).filter_by(userid=session.get(USERID)).all()}
        base_name = "Neues Profil"
        candidate_name = base_name
        counter = 2
        while candidate_name in existing_names:
            candidate_name = f"{base_name} {counter}"
            counter += 1

        next_pos = (db.session.query(func.max(profiles.position)).filter_by(userid=session.get(USERID)).scalar() or 0) + 1
        new_p = profiles(
            userid=session.get(USERID),
            name=candidate_name,
            maxhours=Decimal("0.00"),
            visible=True,
            position=next_pos,
            color=None,
        )
        db.session.add(new_p)
        db.session.commit()

        if wants_json:
            return jsonify(
                success=True,
                profile={
                    "id": new_p.id,
                    "name": new_p.name,
                    "color": new_p.color or "",
                    "visible": new_p.visible
                }
            )
        return redirect(url_for('profile.profile'))

    profile_id = request.form.get('profile_id', type=int)
    prof = db.session.query(profiles).filter_by(
        id=profile_id, userid=session.get(USERID)
    ).first()
    if prof is None:
        if wants_json:
            return jsonify(error="Arbeitsprofil nicht gefunden"), 404
        return redirect(url_for('profile.profile', profile_message="Arbeitsprofil nicht gefunden"))

    if action == 'rename':
        name = (request.form.get('name') or '').strip()
        if not name or len(name) > 30:
            message = "Der Profilname muss zwischen 1 und 30 Zeichen lang sein"
            if wants_json:
                return jsonify(error=message), 400
        elif db.session.query(profiles).filter(
            profiles.userid == session.get(USERID),
            profiles.name == name,
            profiles.id != prof.id,
        ).first():
            message = "Dieses Arbeitsprofil existiert bereits"
            if wants_json:
                return jsonify(error=message), 409
        else:
            prof.name = name
            db.session.commit()
            message = "Arbeitsprofil umbenannt"
            if wants_json:
                return jsonify(success=True, message=message, name=prof.name)
    elif action == 'set_color':
        new_color = (request.form.get('color') or '').strip()
        if new_color and re.match(r'^#[0-9a-fA-F]{6}$', new_color):
            prof.color = new_color
        elif not new_color:
            prof.color = None
        else:
            message = "Ungültiger Farbcode"
            if wants_json:
                return jsonify(error=message), 400
            return redirect(url_for('profile.profile', profile_message=message))
        db.session.commit()
        message = "Profilfarbe gespeichert"
        if wants_json:
            return jsonify(success=True, message=message, color=prof.color)
    elif action == 'toggle-visibility':
        if prof.visible and db.session.query(profiles).filter_by(
            userid=session.get(USERID), visible=True
        ).count() <= 1:
            message = "Mindestens ein Arbeitsprofil muss sichtbar bleiben"
            if wants_json:
                return jsonify(error=message), 400
        else:
            prof.visible = not prof.visible
            if not prof.visible and session.get(PROFILEID) == prof.id:
                replacement = db.session.query(profiles).filter(
                    profiles.userid == session.get(USERID),
                    profiles.id != prof.id,
                    profiles.visible.is_(True),
                ).order_by(profiles.id).first()
                if replacement:
                    session[PROFILEID] = replacement.id
                    user = db.session.query(users).filter_by(id=session.get(USERID)).first()
                    if user:
                        user.last_profile_id = replacement.id
            db.session.commit()
            message = "Arbeitsprofil ausgeblendet" if not prof.visible else "Arbeitsprofil eingeblendet"
            if wants_json:
                return jsonify(success=True, message=message, visible=prof.visible)
    elif action == 'delete':
        if db.session.query(profiles).filter_by(userid=session.get(USERID)).count() <= 1:
            message = "Das letzte Arbeitsprofil kann nicht gelöscht werden"
            if wants_json:
                return jsonify(error=message), 400
        else:
            was_active = session.get(PROFILEID) == prof.id
            db.session.query(data).filter_by(profileid=prof.id).delete()
            db.session.query(category).filter_by(profileid=prof.id).delete()
            db.session.delete(prof)
            if was_active:
                replacement = db.session.query(profiles).filter(
                    profiles.userid == session.get(USERID),
                    profiles.id != prof.id,
                    profiles.visible.is_(True),
                ).order_by(profiles.id).first()
                if replacement:
                    session[PROFILEID] = replacement.id
                    user = db.session.query(users).filter_by(id=session.get(USERID)).first()
                    if user:
                        user.last_profile_id = replacement.id
            db.session.commit()
            message = "Arbeitsprofil gelöscht"
            if wants_json:
                return jsonify(success=True, message=message, deleted=True)
    else:
        message = "Unbekannte Arbeitsprofil-Aktion"
        if wants_json:
            return jsonify(error=message), 400

    return redirect(url_for('profile.profile', profile_message=message))


@profile_bp.route('/export', methods=['POST'])
@validTokenChecker
def export_data():
    current_user_id = session.get(USERID)
    export_format = (request.form.get('format') or 'pdf').strip().lower()
    selected_profile_ids_raw = request.form.getlist('profile_ids')

    selected_ids = []
    for pid in selected_profile_ids_raw:
        try:
            selected_ids.append(int(pid))
        except (ValueError, TypeError):
            pass

    user_profiles = db.session.query(profiles).filter(
        profiles.userid == current_user_id,
        profiles.id.in_(selected_ids)
    ).order_by(profiles.position).all()

    if not user_profiles:
        return redirect(url_for('profile.profile', profile_message="Bitte wähle mindestens ein Profil für den Export aus."))

    profile_id_to_name = {p.id: p.name for p in user_profiles}
    profile_names = [p.name for p in user_profiles]
    current_lang = session.get('lang', DEFAULT_LANGUAGE)

    entries_query = db.session.query(data).filter(
        data.profileid.in_([p.id for p in user_profiles]),
        data.data.isnot(None),
        data.data > 0
    ).order_by(data.date.asc(), data.profileid.asc()).all()

    grouped_months: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
    month_totals: Dict[Tuple[int, int], Decimal] = {}

    for entry in entries_query:
        key = (entry.date.year, entry.date.month)
        if key not in grouped_months:
            grouped_months[key] = []
            month_totals[key] = Decimal('0')

        grouped_months[key].append({
            'date': entry.date,
            'hours': entry.data,
            'profile_name': profile_id_to_name.get(entry.profileid, '')
        })
        month_totals[key] += (entry.data or Decimal('0'))

    if not grouped_months:
        now_date = date.today()
        grouped_months[(now_date.year, now_date.month)] = []
        month_totals[(now_date.year, now_date.month)] = Decimal('0')

    sorted_keys = sorted(grouped_months.keys())
    monthly_data = []
    for (year, month) in sorted_keys:
        monthly_data.append({
            'year': year,
            'month': month,
            'month_name': get_month_name(month, current_lang),
            'total_hours': month_totals.get((year, month), Decimal('0')),
            'entries': grouped_months[(year, month)]
        })

    user_obj = get_current_user()
    user_name = user_obj.username if user_obj else "Benutzer"
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")

    profile_accent_color = None
    for p in user_profiles:
        if p.color:
            profile_accent_color = p.color
            break

    if export_format == 'excel':
        excel_buffer = generate_excel_export(
            profile_names=profile_names,
            monthly_data=monthly_data,
            user_name=user_name,
            lang=current_lang,
            accent_color=profile_accent_color
        )
        safe_name = "Arbeitszeiten" if len(profile_names) > 1 else secure_filename(profile_names[0])
        filename = f"{safe_name}_{timestamp_str}.xlsx"
        return send_file(
            excel_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        pdf_buffer = generate_pdf_export(
            profile_names=profile_names,
            monthly_data=monthly_data,
            user_name=user_name,
            lang=current_lang,
            accent_color=profile_accent_color
        )
        safe_name = "Arbeitszeiten" if len(profile_names) > 1 else secure_filename(profile_names[0])
        filename = f"{safe_name}_{timestamp_str}.pdf"
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )


@profile_bp.route('/set-language', methods=['POST'])
@csrf.exempt
def set_language():
    lang = (request.form.get('language') or (request.get_json(silent=True) or {}).get('language') or '').strip().lower()
    if lang in SUPPORTED_LANGUAGES:
        session['lang'] = lang
        user_id = session.get(USERID)
        if user_id:
            user = db.session.query(users).filter_by(id=user_id).first()
            if user:
                user.language = lang
                db.session.commit()

    wants_json = request.headers.get("X-Requested-With") == "fetch" or request.is_json
    if wants_json:
        return jsonify(success=True, language=lang)

    resp = redirect(get_safe_redirect_url("profile.profile"))
    if lang in SUPPORTED_LANGUAGES:
        resp.set_cookie('lang', lang, max_age=365 * 24 * 3600, samesite='Lax')
    return resp


@profile_bp.route('/set-theme', methods=['POST'])
@csrf.exempt
def set_theme():
    theme = (request.form.get('theme') or (request.get_json(silent=True) or {}).get('theme') or '').strip().lower()
    if theme in SUPPORTED_THEMES:
        session['theme'] = theme
        user_id = session.get(USERID)
        if user_id:
            user = db.session.query(users).filter_by(id=user_id).first()
            if user:
                user.theme = theme
                db.session.commit()

    wants_json = request.headers.get("X-Requested-With") == "fetch" or request.is_json
    if wants_json:
        return jsonify(success=True, theme=theme)

    resp = redirect(get_safe_redirect_url("profile.profile"))
    if theme in SUPPORTED_THEMES:
        resp.set_cookie('theme', theme, max_age=365 * 24 * 3600, samesite='Lax')
    return resp
