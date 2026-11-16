import re
from datetime import date
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, redirect, request, session, url_for, jsonify
from sqlalchemy import func
from models import db, users, profiles, data
from constants import USERID, PROFILEID
from login import validTokenChecker
from utils.session_helpers import (
    get_active_profile, get_username, get_active_profile_name,
    get_profile_list,
)
from utils.profile_images import get_profile_image_url
from utils.home_service import (
    build_home_context, build_home_json_state, get_previous_effective_maxhours,
)

home_bp = Blueprint('home', __name__)


@home_bp.route('/home', methods=["GET", "POST"])
@validTokenChecker
def home():
    active_profile = get_active_profile()
    user_id = active_profile.id if active_profile else None
    wants_json = request.headers.get("X-Requested-With") == "fetch" or request.accept_mimetypes.best == "application/json"

    def parse_selected_date(date_string):
        if date_string:
            from datetime import datetime
            try:
                return datetime.strptime(date_string, '%Y-%m-%d').date()
            except ValueError:
                pass
        return date.today()

    if request.method == "POST":
        action = request.form.get('action')
        selected_date_str = request.form.get('selected_date') or request.args.get('date')
        selected_date = parse_selected_date(selected_date_str)
        day_delta = Decimal('0')
        total_hours_delta = None

        try:
            if action == 'set_max_hours':
                max_hours_str = request.form.get('max_hours', '').strip().replace(',', '.')
                if ':' in max_hours_str:
                    hours, minutes = max_hours_str.split(':', 1)
                    max_hours = Decimal(hours) + (Decimal(minutes) / Decimal('60'))
                else:
                    max_hours = Decimal(max_hours_str) if max_hours_str else None
                if max_hours is not None and not (Decimal('0') < max_hours <= Decimal('999.99')):
                    raise ValueError("Monatsstunden müssen zwischen 0,01 und 999,99 liegen")
                first_of_month = selected_date.replace(day=1)
                previous_effective_maxhours = get_previous_effective_maxhours(user_id, selected_date)
                stored_max_hours = max_hours

                if max_hours is not None and previous_effective_maxhours is not None and max_hours == previous_effective_maxhours:
                    stored_max_hours = None

                existing_entry = db.session.query(data).filter(
                    data.profileid == user_id,
                    data.date == first_of_month
                ).first()

                if stored_max_hours is None:
                    if existing_entry:
                        existing_entry.maxhours = None
                        if existing_entry.data is None and existing_entry.categoryid is None:
                            db.session.delete(existing_entry)
                elif existing_entry:
                    existing_entry.maxhours = stored_max_hours
                else:
                    db.session.add(data(
                        userid=session.get(USERID),
                        profileid=user_id,
                        date=first_of_month,
                        categoryid=None,
                        data=None,
                        maxhours=stored_max_hours
                    ))

                db.session.commit()

                if wants_json:
                    home_context = build_home_context(user_id, selected_date, include_total_hours=True, include_overview=False)
                    response_state = build_home_json_state(home_context)
                    return jsonify(response_state)

                return redirect(f"/home?date={selected_date.isoformat()}")

            elif action in ['add_30', 'sub_30']:
                current_entry = db.session.query(data).filter(
                    data.profileid == user_id,
                    data.date == selected_date
                ).first()
                current_total = current_entry.data if current_entry and current_entry.data is not None else Decimal('0')
                current_maxhours = current_entry.maxhours if current_entry else None

                day_delta = Decimal('0.5') if action == 'add_30' else -Decimal('0.5')
                new_total = current_total + day_delta

                if new_total < 0:
                    day_delta = -current_total
                    new_total = Decimal('0')

                db.session.query(data).filter(
                    data.profileid == user_id,
                    data.date == selected_date
                ).delete()

                if new_total > 0 or current_maxhours is not None:
                    db.session.add(data(
                        userid=session.get(USERID),
                        profileid=user_id,
                        date=selected_date,
                        categoryid=None,
                        data=new_total if new_total > 0 else None,
                        maxhours=current_maxhours
                    ))

            elif action == 'set_time':
                time_value = request.form.get('time_value')

                if time_value:
                    time_parts = time_value.split(':')
                    if len(time_parts) == 2:
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1])
                        if not (0 <= hours <= 24 and 0 <= minutes < 60) or (hours == 24 and minutes > 0):
                            raise ValueError("Tagesarbeitszeit muss zwischen 00:00 und 24:00 liegen")
                        decimal_hours = Decimal(hours) + Decimal(minutes) / Decimal(60)

                        current_entry = db.session.query(data).filter(
                            data.profileid == user_id,
                            data.date == selected_date
                        ).first()
                        current_total = current_entry.data if current_entry and current_entry.data is not None else Decimal('0')
                        current_maxhours = current_entry.maxhours if current_entry else None
                        day_delta = decimal_hours - current_total

                        db.session.query(data).filter(
                            data.profileid == user_id,
                            data.date == selected_date
                        ).delete()

                        if decimal_hours > 0 or current_maxhours is not None:
                            db.session.add(data(
                                userid=session.get(USERID),
                                profileid=user_id,
                                date=selected_date,
                                categoryid=None,
                                data=decimal_hours if decimal_hours > 0 else None,
                                maxhours=current_maxhours
                            ))

            db.session.commit()

        except (ValueError, InvalidOperation, Exception) as e:
            print(f"Error processing home POST: {e}")
            db.session.rollback()
            if wants_json:
                return jsonify({"error": "action could not be saved"}), 400

        if wants_json:
            home_context = build_home_context(user_id, selected_date, include_total_hours=True, include_overview=False)
            response_state = build_home_json_state(home_context)

            if action in ['add_30', 'sub_30', 'set_time']:
                response_state['day_total_hours_delta'] = float(day_delta)
                response_state['data_changed'] = True

            elif action == 'set_max_hours':
                response_state['data_changed'] = True

            return jsonify(response_state)

        return redirect(f"/home?date={selected_date.isoformat()}")

    selected_date = parse_selected_date(request.args.get('date', ''))
    include_overview = request.args.get('include_overview') == '1'
    home_context = build_home_context(
        user_id,
        selected_date,
        include_total_hours=not wants_json,
        include_overview=include_overview if wants_json else False
    )

    if wants_json:
        return jsonify(build_home_json_state(home_context))

    return render_template(
        'home.html',
        user_id=user_id,
        get_username=get_username,
        get_active_profile_name=get_active_profile_name,
        profile_image_url=get_profile_image_url(),
        selected_date=home_context['selected_date'],
        selected_date_display=home_context['selected_date_display'],
        selected_month_name=home_context['selected_month_name'],
        current_max_hours=home_context['current_max_hours_display'],
        current_max_hours_numeric=home_context['current_max_hours_numeric'],
        suggested_max_hours=home_context['suggested_max_hours_display'],
        total_hours=home_context['total_hours'],
        total_hours_numeric=home_context['total_hours_numeric'],
        month_hours=home_context['month_hours'],
        month_hours_numeric=home_context['month_hours_numeric'],
        overview_data=home_context['overview_data'],
        edit_time=home_context['edit_time'],
        edit_time_24h=home_context['edit_time_24h'],
        profiles=get_profile_list(), active_profile_id=user_id,
        active_profile=active_profile
    )


@home_bp.route('/profiles/switch', methods=['POST'])
@validTokenChecker
def switch_profile():
    profile_id = request.form.get('profile_id', type=int)
    profile = db.session.query(profiles).filter_by(
        id=profile_id, userid=session.get(USERID), visible=True
    ).first()
    if profile is None:
        return jsonify(error="Profil nicht gefunden"), 404
    session[PROFILEID] = profile.id
    user = db.session.query(users).filter_by(id=session.get(USERID)).first()
    if user:
        user.last_profile_id = profile.id
        db.session.commit()
    return redirect(url_for('home.home'))


@home_bp.route('/profiles/create', methods=['POST'])
@validTokenChecker
def create_profile():
    name = (request.form.get('name') or '').strip()
    maxhours_value = (request.form.get('maxhours') or '').strip().replace(',', '.')
    color_val = (request.form.get('color') or '').strip()
    if not name or len(name) > 30:
        return jsonify(error="Der Profilname muss zwischen 1 und 30 Zeichen lang sein"), 400
    try:
        maxhours = Decimal(maxhours_value)
    except InvalidOperation:
        return jsonify(error="Bitte gültige Monatsstunden angeben"), 400
    if maxhours <= 0 or maxhours > Decimal("999.99"):
        return jsonify(error="Die Monatsstunden müssen zwischen 0,01 und 999,99 liegen"), 400

    clean_color = None
    if color_val:
        if re.match(r'^#[0-9a-fA-F]{6}$', color_val):
            clean_color = color_val

    if db.session.query(profiles).filter_by(userid=session.get(USERID), name=name).first():
        return jsonify(error="Dieses Profil existiert bereits"), 409
    next_pos = (db.session.query(func.max(profiles.position)).filter_by(userid=session.get(USERID)).scalar() or 0) + 1
    profile = profiles(
        userid=session.get(USERID),
        name=name,
        maxhours=maxhours,
        visible=True,
        position=next_pos,
        color=clean_color,
    )
    db.session.add(profile)
    db.session.commit()
    session[PROFILEID] = profile.id
    user = db.session.query(users).filter_by(id=session.get(USERID)).first()
    if user:
        user.last_profile_id = profile.id
        db.session.commit()
    return redirect(url_for('home.home'))


@home_bp.route('/count', methods=['GET'])
@validTokenChecker
def count_entries():  # sourcery skip: use-named-expression
    from sqlalchemy import distinct
    user = db.session.query(users).filter(users.id == session.get(USERID)).first()
    if user:
        count = db.session.query(func.count(distinct(data.date))).filter(
            data.profileid == session.get(PROFILEID)
        ).scalar()
        return jsonify(count=count)
    else:
        return jsonify(error="User not found"), 404
