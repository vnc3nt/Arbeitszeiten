from flask import Flask, render_template, url_for, redirect, request, jsonify, session, send_file
from datetime import datetime, date
from models import db, users, profiles, token, data, category
import os
from api import app as api_app
from login import change_password, change_username, check_username, checkuser, delete_account, loginChecker, validTokenChecker, logoutUser, checkRegistration, hash_pw
import secrets
from constants import USERID, TOKEN, PROFILEID
from time import time
from sqlalchemy import func, distinct, text
from decimal import Decimal, InvalidOperation
from werkzeug.utils import secure_filename

if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f.readlines():
            if line.strip() and not line.strip().startswith("#"):
                attr, val = line.lstrip().split("=", 1)
                os.environ[attr] = val.rstrip("\n")
else:
    print("Keine .env Datei gefunden, nutze Cloud-Umgebungsvariablen.")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://{}.{}:{}@{}:{}/{}".format(
    os.environ.get("uname"),
    os.environ.get("db"),
    os.environ.get("password"),
    os.environ.get("host"),
    os.environ.get("port"),
    os.environ.get("scheme")
)
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {
        "options": "-csearch_path=arbeitszeiten,public"
    }
}
app.config.update(
    BUNDLE_ERRORS = True,
    SECRET_KEY = os.environ.get("SECRET_KEY"),
    SESSION_COOKIE_SECURE = True,  # Cloud Run nutzt HTTPS, also auf True setzen, bei render hatte ich False
    SESSION_COOKIE_SAMESITE = "Lax" # "Lax" ist oft kompatibler als "Strict" für Redirects
)

PROFILE_IMAGE_DEFAULT = "img/icons/512x512-profile.png"
PROFILE_IMAGE_FOLDER = os.path.join("uploads", "profile_images")
PROFILE_IMAGE_ABS_FOLDER = os.path.join(app.static_folder, PROFILE_IMAGE_FOLDER)
PROFILE_IMAGE_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
PROFILE_IMAGE_MAX_SIZE = 2 * 1024 * 1024

#print(app.config["SQLALCHEMY_DATABASE_URI"])

app.register_blueprint(api_app)

# Jinja2-Filter für deutsche Zahlenformatierung
@app.template_filter('decimal_comma')
def decimal_comma_filter(value):
    """Ersetzt Punkt mit Komma als Dezimaltrennzeichen für deutsche Zahlenformatierung"""
    if value is None:
        return value
    # Konvertiere zu String und ersetze Punkt mit Komma
    return str(value).replace('.', ',')


def get_month_start(target_date):
    return target_date.replace(day=1)


def get_next_month_start(target_date):
    month_start = get_month_start(target_date)
    if month_start.month == 12:
        return month_start.replace(year=month_start.year + 1, month=1)
    return month_start.replace(month=month_start.month + 1)


def get_month_total_hours(user_id, target_date):
    month_start = get_month_start(target_date)
    next_month_start = get_next_month_start(target_date)
    return db.session.query(func.sum(data.data)).filter(
        data.profileid == user_id,
        data.date >= month_start,
        data.date < next_month_start
    ).scalar() or Decimal('0')


def get_effective_maxhours_for_month(user_id, target_date):
    first_of_month = get_month_start(target_date)
    max_hours = db.session.query(data.maxhours).filter(
        data.profileid == user_id,
        data.date <= first_of_month,
        data.maxhours.isnot(None)
    ).order_by(data.date.desc()).limit(1).scalar()
    if max_hours is not None:
        return max_hours
    profile = db.session.query(profiles).filter_by(id=user_id).first()
    return profile.maxhours if profile and profile.maxhours else None


def get_previous_effective_maxhours(user_id, target_date):
    first_of_month = get_month_start(target_date)
    return db.session.query(data.maxhours).filter(
        data.profileid == user_id,
        data.date < first_of_month,
        data.maxhours.isnot(None)
    ).order_by(data.date.desc()).limit(1).scalar()


def format_decimal_hours(decimal_hours):
    if decimal_hours == int(decimal_hours):
        return str(int(decimal_hours))
    return str(float(decimal_hours)).replace('.', ',')


def format_hours(decimal_hours):
    if decimal_hours == 0:
        return "0:00"
    hours = int(decimal_hours)
    minutes = int((decimal_hours - hours) * 60)
    return f"{hours}:{minutes:02d}"


def format_time_24h(decimal_hours):
    if decimal_hours == 0:
        return "00:00"
    hours = int(decimal_hours)
    minutes = int((decimal_hours - hours) * 60)
    return f"{hours:02d}:{minutes:02d}"


def format_total_hours_with_sign(decimal_hours):
    if decimal_hours == 0:
        return "0"
    if decimal_hours > 0:
        if decimal_hours == int(decimal_hours):
            return f"+{int(decimal_hours)}"
        return f"+{float(decimal_hours)}".replace('.', ',')
    if decimal_hours == int(decimal_hours):
        return str(int(decimal_hours))
    return str(float(decimal_hours)).replace('.', ',')


def serialize_overview_data(overview_data):
    serialized = {}

    for year, months in overview_data.items():
        serialized_year = {}
        for month, month_data in months.items():
            serialized_year[month] = {
                'name': month_data['name'],
                'total_hours': float(month_data['total_hours']),
                'max_hours': float(month_data['max_hours']) if month_data['max_hours'] is not None else None,
                'difference': float(month_data['difference']) if month_data['difference'] is not None else None,
                'entries': [
                    {
                        'date': entry['date'].isoformat(),
                        'hours': float(entry['hours'])
                    }
                    for entry in month_data['entries']
                ]
            }
        serialized[year] = serialized_year

    return serialized


def ensure_profile_image_column():
    column_exists = db.session.execute(text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'arbeitszeiten'
          AND table_name = 'users'
          AND column_name = 'profile_image'
    """)).first()

    if column_exists:
        return

    db.session.execute(text("ALTER TABLE arbeitszeiten.users ADD COLUMN profile_image VARCHAR(255)"))
    db.session.commit()


def ensure_profiles():
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS arbeitszeiten.profiles (
            id BIGINT PRIMARY KEY,
            userid BIGINT NOT NULL REFERENCES arbeitszeiten.users(id),
            name VARCHAR(30) NOT NULL,
            maxhours NUMERIC(5, 2) NOT NULL DEFAULT 0,
            visible BOOLEAN NOT NULL DEFAULT TRUE,
            CONSTRAINT uq_profiles_user_name UNIQUE (userid, name)
        )
    """))
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.data ADD COLUMN IF NOT EXISTS profileid BIGINT")
    )
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.category ADD COLUMN IF NOT EXISTS profileid BIGINT")
    )
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.profiles ADD COLUMN IF NOT EXISTS maxhours NUMERIC(5, 2) NOT NULL DEFAULT 0")
    )
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.profiles ADD COLUMN IF NOT EXISTS visible BOOLEAN NOT NULL DEFAULT TRUE")
    )
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.profiles DROP COLUMN IF EXISTS profile_image")
    )
    db.session.execute(text("ALTER TABLE arbeitszeiten.data DROP CONSTRAINT IF EXISTS data_pkey"))
    for user in db.session.query(users).all():
        default_profile = db.session.query(profiles).filter_by(
            userid=user.id, name="Standardprofil"
        ).first()
        if default_profile is None:
            default_profile = db.session.query(profiles).filter_by(
                userid=user.id
            ).order_by(profiles.id).first()
            if default_profile is not None:
                default_profile.name = "Standardprofil"
        if default_profile is None:
            next_id = db.session.query(func.max(profiles.id)).scalar() or 0
            default_profile = profiles(
                id=next_id + 1,
                userid=user.id,
                name="Standardprofil",
                maxhours=0,
            )
            db.session.add(default_profile)
            db.session.flush()
        db.session.execute(text("""
            UPDATE arbeitszeiten.data d
            SET profileid = p.id
            FROM arbeitszeiten.profiles p
            WHERE d.userid = p.userid
              AND d.profileid IS NULL
              AND p.name = 'Standardprofil'
        """))
        db.session.execute(text("""
            UPDATE arbeitszeiten.category c
            SET profileid = p.id
            FROM arbeitszeiten.profiles p
            WHERE c.userid = p.userid
              AND c.profileid IS NULL
              AND p.name = 'Standardprofil'
        """))
    db.session.execute(text("""
        ALTER TABLE arbeitszeiten.data
        ADD CONSTRAINT data_pkey PRIMARY KEY (userid, date, profileid)
    """))
    db.session.commit()


def get_active_profile():
    profile_id = session.get(PROFILEID)
    account_id = session.get(USERID)
    profile = db.session.query(profiles).filter(
        profiles.id == profile_id,
        profiles.userid == account_id,
        profiles.visible.is_(True),
    ).first()
    if profile is None and account_id is not None:
        profile = db.session.query(profiles).filter_by(userid=account_id).order_by(profiles.id).first()
        if profile:
            session[PROFILEID] = profile.id
    return profile


def get_profile_list():
    return db.session.query(profiles).filter_by(
        userid=session.get(USERID), visible=True
    ).order_by(profiles.id).all()


def get_all_profile_list():
    return db.session.query(profiles).filter_by(
        userid=session.get(USERID)
    ).order_by(profiles.id).all()


def get_active_profile_name():
    profile = get_active_profile()
    return profile.name if profile else get_username()


def allowed_profile_image(filename: str) -> bool:
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in PROFILE_IMAGE_ALLOWED_EXTENSIONS


def get_current_user():
    return db.session.query(users).filter(users.id == session.get(USERID)).first()


def get_profile_image_url() -> str:
    user = get_current_user()
    if user and user.profile_image:
        absolute_path = os.path.join(app.static_folder, user.profile_image)
        if os.path.exists(absolute_path):
            return url_for("static", filename=user.profile_image)

    return url_for("static", filename=PROFILE_IMAGE_DEFAULT)


def remove_profile_image_file(profile_image_path):
    if not profile_image_path:
        return

    absolute_path = os.path.join(app.static_folder, profile_image_path)
    if os.path.exists(absolute_path):
        os.remove(absolute_path)


def save_profile_image(uploaded_file, user):
    if uploaded_file is None or not uploaded_file.filename:
        return "Bitte eine Bilddatei auswählen"

    if not allowed_profile_image(uploaded_file.filename):
        return "Nur PNG, JPG oder WEBP sind erlaubt"

    uploaded_file.stream.seek(0, os.SEEK_END)
    file_size = uploaded_file.stream.tell()
    uploaded_file.stream.seek(0)

    if file_size > PROFILE_IMAGE_MAX_SIZE:
        return "Die Datei darf maximal 2 MB groß sein"

    extension = uploaded_file.filename.rsplit(".", 1)[1].lower()
    if extension == "jpeg":
        extension = "jpg"

    os.makedirs(PROFILE_IMAGE_ABS_FOLDER, exist_ok=True)

    previous_profile_image = user.profile_image

    filename = secure_filename(f"profile_{user.id}.{extension}")
    relative_path = os.path.join(PROFILE_IMAGE_FOLDER, filename).replace("\\", "/")
    absolute_path = os.path.join(app.static_folder, relative_path)

    try:
        uploaded_file.save(absolute_path)
        user.profile_image = relative_path
        db.session.commit()
    except Exception:
        db.session.rollback()
        if os.path.exists(absolute_path):
            os.remove(absolute_path)
        return "Profilbild konnte nicht gespeichert werden"

    if previous_profile_image and previous_profile_image != relative_path:
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

    remove_profile_image_file(previous_profile_image)
    return None


def build_home_context(user_id, selected_date, include_total_hours=True, include_overview=True):
    german_months = {
        1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
        5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
    }

    month_maxhours_cache = {}
    month_hours_cache = {}

    def cached_month_maxhours(target_month):
        month_key = target_month.isoformat()
        if month_key not in month_maxhours_cache:
            month_maxhours_cache[month_key] = get_effective_maxhours_for_month(user_id, target_month)
        return month_maxhours_cache[month_key]

    def cached_month_hours(target_month):
        month_key = target_month.isoformat()
        if month_key not in month_hours_cache:
            month_hours_cache[month_key] = get_month_total_hours(user_id, target_month)
        return month_hours_cache[month_key]

    selected_date_str = selected_date.isoformat()
    selected_date_display = 'Heute' if selected_date == date.today() else selected_date.strftime('%d.%m.%Y')

    day_total_hours = db.session.query(func.sum(data.data)).filter(
        data.profileid == user_id,
        data.date == selected_date
    ).scalar() or Decimal('0')

    month_hours_decimal = cached_month_hours(selected_date)

    current_max_hours = cached_month_maxhours(selected_date)
    current_max_hours_display = format_decimal_hours(current_max_hours) if current_max_hours is not None else None
    suggested_max_hours_display = current_max_hours_display or ""

    def calculate_total_deficit():
        if not include_total_hours:
            return None

        earliest_entry = db.session.query(func.min(data.date)).filter(
            data.profileid == user_id,
            (data.data.isnot(None) | data.maxhours.isnot(None))
        ).scalar()

        if earliest_entry is None:
            return Decimal('0')

        total_deficit = Decimal('0')
        current_month = earliest_entry.replace(day=1)
        end_month = date.today().replace(day=1)

        while current_month <= end_month:
            current_maxhours = cached_month_maxhours(current_month)

            if current_maxhours is not None:
                month_actual_hours = cached_month_hours(current_month)
                total_deficit += month_actual_hours - current_maxhours

            current_month = get_next_month_start(current_month)

        return total_deficit

    def create_overview_data():
        if not include_overview:
            return None

        earliest_entry = db.session.query(func.min(data.date)).filter(
            data.profileid == user_id,
            (data.data.isnot(None) | data.maxhours.isnot(None))
        ).scalar()

        if earliest_entry is None:
            return {}

        all_entries = db.session.query(data).filter(
            data.profileid == user_id,
            (data.data.isnot(None) | data.maxhours.isnot(None))
        ).order_by(data.date.desc()).all()

        overview_data = {}
        current_month = earliest_entry.replace(day=1)
        end_month = date.today().replace(day=1)

        while current_month <= end_month:
            year = current_month.year
            month = current_month.month

            if year not in overview_data:
                overview_data[year] = {}

            if month not in overview_data[year]:
                overview_data[year][month] = {}

            month_maxhours = cached_month_maxhours(current_month)
            month_total = cached_month_hours(current_month)

            month_difference = None
            if month_maxhours is not None:
                month_difference = month_total - month_maxhours

            overview_data[year][month] = {
                'name': german_months[month],
                'total_hours': month_total,
                'max_hours': month_maxhours,
                'difference': month_difference,
                'entries': []
            }

            current_month = get_next_month_start(current_month)

        for entry in all_entries:
            year = entry.date.year
            month = entry.date.month

            if entry.data is not None and entry.data > 0 and year in overview_data and month in overview_data[year]:
                overview_data[year][month]['entries'].append({
                    'date': entry.date,
                    'hours': entry.data
                })

        return overview_data

    total_deficit = calculate_total_deficit()
    overview_data = create_overview_data()

    return {
        'selected_date': selected_date_str,
        'selected_date_display': selected_date_display,
        'selected_month_name': german_months[selected_date.month],
        'day_total_hours': day_total_hours,
        'edit_time': format_hours(day_total_hours),
        'edit_time_24h': format_time_24h(day_total_hours),
        'current_max_hours': current_max_hours,
        'current_max_hours_display': current_max_hours_display,
        'current_max_hours_numeric': float(current_max_hours) if current_max_hours is not None else 0,
        'suggested_max_hours_display': suggested_max_hours_display,
        'total_hours': format_total_hours_with_sign(total_deficit) if total_deficit is not None else None,
        'total_hours_numeric': float(total_deficit) if total_deficit is not None else None,
        'month_hours': format_decimal_hours(month_hours_decimal),
        'month_hours_numeric': float(month_hours_decimal),
        'overview_data': overview_data,
    }


def build_home_json_state(home_context):
    response = {
        'selected_date': home_context['selected_date'],
        'selected_date_display': home_context['selected_date_display'],
        'selected_month_name': home_context['selected_month_name'],
        'edit_time': home_context['edit_time'],
        'edit_time_24h': home_context['edit_time_24h'],
        'current_max_hours_display': home_context['current_max_hours_display'],
        'current_max_hours_numeric': home_context['current_max_hours_numeric'],
        'suggested_max_hours_display': home_context['suggested_max_hours_display'],
        'month_hours': home_context['month_hours'],
        'month_hours_numeric': home_context['month_hours_numeric'],
        'day_total_hours': float(home_context['day_total_hours']),
    }

    if home_context.get('total_hours') is not None:
        response['total_hours'] = home_context['total_hours']
        response['total_hours_numeric'] = home_context['total_hours_numeric']

    if home_context.get('overview_data') is not None:
        response['overview_data'] = serialize_overview_data(home_context['overview_data'])

    return response

db.init_app(app)

with app.app_context():
    db.create_all()
    ensure_profile_image_column()
    ensure_profiles()

@app.route('/')
def index():
    return redirect("/login")

@app.route('/login',methods=["GET","POST"])
@loginChecker
def login():
    if request.method == "POST":
        username = request.form.get("username_input")
        password = request.form.get("password_input")
        if username is not None and password is not None and checkuser(username, password):
            # successful logged in
            # token cleanup
            for everySession in db.session.query(token).filter(token.expiretime < time()):
                db.session.delete(everySession)
            session[USERID] = db.session.query(users).filter(users.username==username).first().id
            default_profile = db.session.query(profiles).filter_by(userid=session[USERID]).order_by(profiles.id).first()
            if default_profile:
                session[PROFILEID] = default_profile.id
            newToken = token(userid=session[USERID], token=secrets.token_urlsafe(96)) # 96 always produces a 128-long string, but idk why
            session[TOKEN] = newToken.token
            db.session.add(newToken)
            db.session.commit()
            return redirect("/home")
    return render_template('login.html')

@app.route('/register',methods=["GET","POST"])
def register():
    if request.method == "POST":
        username_input = request.form.get("username_input")
        password_1 = request.form.get("password_input_1")
        password_2 = request.form.get("password_input_2")
        terms_checkbox = request.form.get("terms_checkbox")
        
        # Check if terms checkbox is checked
        if not terms_checkbox:
            # You could add a flash message here for better UX
            return render_template('register.html', error="Sie müssen den Datenschutzbestimmungen zustimmen.")
        
        if username_input is not None and password_1 is not None and password_2 is not None and checkRegistration(username_input, password_1, password_2) and check_username(username_input):
            # successful logged in
            # token cleanup
            last_id = db.session.query(func.max(users.id)).scalar()
            newUserId = (last_id or 0) + 1
            newUser = users(id=newUserId, username=username_input, password=hash_pw(password_1))
            db.session.add(newUser)
            db.session.commit()
            db.session.add(profiles(
                id=newUserId,
                userid=newUserId,
                name="Standardprofil",
                maxhours=0,
                visible=True,
            ))
            db.session.commit()
            return redirect("/login")
    return render_template('register.html')

@app.route('/home', methods=["GET", "POST"])
@validTokenChecker
def home():
    active_profile = get_active_profile()
    user_id = active_profile.id if active_profile else None
    wants_json = request.headers.get("X-Requested-With") == "fetch" or request.accept_mimetypes.best == "application/json"

    def parse_selected_date(date_string):
        if date_string:
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
                max_hours_str = request.form.get('max_hours', '').replace(',', '.')
                max_hours = Decimal(max_hours_str) if max_hours_str else None
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
            # GEÄNDERT: Wir zwingen den Server IMMER include_total_hours=True zu nutzen
            home_context = build_home_context(user_id, selected_date, include_total_hours=True, include_overview=False)
            response_state = build_home_json_state(home_context)

            if action in ['add_30', 'sub_30', 'set_time']:
                # Wir schicken nur noch die absolute Änderung für den Tagestext mit.
                # Total und Month Deltas sind weg, weil der Server jetzt die echten Endwerte liefert!
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
        profiles=get_profile_list(), active_profile_id=user_id
    )

@app.route('/profiles/switch', methods=['POST'])
@validTokenChecker
def switch_profile():
    profile_id = request.form.get('profile_id', type=int)
    profile = db.session.query(profiles).filter_by(
        id=profile_id, userid=session.get(USERID), visible=True
    ).first()
    if profile is None:
        return jsonify(error="Profil nicht gefunden"), 404
    session[PROFILEID] = profile.id
    return redirect(url_for('home'))

@app.route('/profiles/create', methods=['POST'])
@validTokenChecker
def create_profile():
    name = (request.form.get('name') or '').strip()
    maxhours_value = (request.form.get('maxhours') or '').strip().replace(',', '.')
    if not name or len(name) > 30:
        return jsonify(error="Der Profilname muss zwischen 1 und 30 Zeichen lang sein"), 400
    try:
        maxhours = Decimal(maxhours_value)
    except InvalidOperation:
        return jsonify(error="Bitte gültige Monatsstunden angeben"), 400
    if maxhours <= 0 or maxhours > Decimal("999.99"):
        return jsonify(error="Die Monatsstunden müssen zwischen 0,01 und 999,99 liegen"), 400
    if db.session.query(profiles).filter_by(userid=session.get(USERID), name=name).first():
        return jsonify(error="Dieses Profil existiert bereits"), 409
    next_id = (db.session.query(func.max(profiles.id)).scalar() or 0) + 1
    profile = profiles(
        id=next_id,
        userid=session.get(USERID),
        name=name,
        maxhours=maxhours,
        visible=True,
    )
    db.session.add(profile)
    db.session.commit()
    session[PROFILEID] = profile.id
    return redirect(url_for('home'))

@app.route('/profiles/manage', methods=['POST'])
@validTokenChecker
def manage_profile():
    profile_id = request.form.get('profile_id', type=int)
    action = request.form.get('profile_action')
    profile = db.session.query(profiles).filter_by(
        id=profile_id, userid=session.get(USERID)
    ).first()
    if profile is None:
        return redirect(url_for('profile', profile_message="Arbeitsprofil nicht gefunden"))

    if action == 'rename':
        name = (request.form.get('name') or '').strip()
        if not name or len(name) > 30:
            message = "Der Profilname muss zwischen 1 und 30 Zeichen lang sein"
        elif db.session.query(profiles).filter(
            profiles.userid == session.get(USERID),
            profiles.name == name,
            profiles.id != profile.id,
        ).first():
            message = "Dieses Arbeitsprofil existiert bereits"
        else:
            profile.name = name
            db.session.commit()
            message = "Arbeitsprofil umbenannt"
    elif action == 'toggle-visibility':
        if profile.visible and db.session.query(profiles).filter_by(
            userid=session.get(USERID), visible=True
        ).count() <= 1:
            message = "Mindestens ein Arbeitsprofil muss sichtbar bleiben"
        else:
            profile.visible = not profile.visible
            if not profile.visible and session.get(PROFILEID) == profile.id:
                replacement = db.session.query(profiles).filter(
                    profiles.userid == session.get(USERID),
                    profiles.id != profile.id,
                    profiles.visible.is_(True),
                ).order_by(profiles.id).first()
                if replacement:
                    session[PROFILEID] = replacement.id
            db.session.commit()
            message = "Arbeitsprofil ausgeblendet" if not profile.visible else "Arbeitsprofil eingeblendet"
    elif action == 'delete':
        if db.session.query(profiles).filter_by(userid=session.get(USERID)).count() <= 1:
            message = "Das letzte Arbeitsprofil kann nicht gelöscht werden"
        else:
            was_active = session.get(PROFILEID) == profile.id
            db.session.query(data).filter_by(profileid=profile.id).delete()
            db.session.query(category).filter_by(profileid=profile.id).delete()
            db.session.delete(profile)
            if was_active:
                replacement = db.session.query(profiles).filter(
                    profiles.userid == session.get(USERID),
                    profiles.id != profile.id,
                    profiles.visible.is_(True),
                ).order_by(profiles.id).first()
                if replacement:
                    session[PROFILEID] = replacement.id
            db.session.commit()
            message = "Arbeitsprofil gelöscht"
    else:
        message = "Unbekannte Arbeitsprofil-Aktion"

    return redirect(url_for('profile', profile_message=message))

@app.route('/edit')
@validTokenChecker
def edit():
    return render_template('edit.html', user_id=session.get(USERID), get_username=get_username,
                           get_active_profile_name=get_active_profile_name,
                           profiles=get_profile_list(), active_profile_id=session.get(PROFILEID),
                           all_profiles=get_all_profile_list())

@app.route('/profile', methods=["GET", "POST"])
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
                return redirect(url_for("profile"))

        elif action == "reset-profile-picture":
            user = get_current_user()
            if user:
                result = reset_profile_image(user)
                if result is None:
                    return redirect(url_for("profile"))
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
        print(f"{result=}")
        profile_message = result
    return render_template('profile.html', user_id=session.get(USERID), get_username=get_username,
                           get_active_profile_name=get_active_profile_name,
                           profile_image_url=get_profile_image_url(), profile_message=profile_message,
                           profiles=get_profile_list(), active_profile_id=session.get(PROFILEID),
                           all_profiles=get_all_profile_list())

@app.route("/logout")
def logout():
    token = session.get(TOKEN)
    logoutUser(token)

    return redirect("/login")

@app.route('/count', methods=['GET'])
@validTokenChecker
def count_entries():  # sourcery skip: use-named-expression
    user = db.session.query(users).filter(users.id == session.get(USERID)).first()
    if user:
        count = db.session.query(func.count(distinct(data.date))).filter(
            data.profileid == session.get(PROFILEID)
        ).scalar()
        #print(count)
        return jsonify(count=count)
    else:
        return jsonify(error="User not found"), 404
    

@app.route('/impressum')
def impressum():
    return render_template('impressum.html')

@app.route('/dpa')
def dpa():
    try:
        return send_file('static/docs/dpa.pdf', 
                         as_attachment=True)
    except Exception as e:
        return str(e)


def get_username() -> str:
    user = db.session.query(users).filter(users.id == session.get(USERID)).first()
    return user.username if user else ""

if __name__ == "__main__":
    # Cloud Run gibt den Port über die Umgebungsvariable PORT vor
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("debug", False) == "True")
