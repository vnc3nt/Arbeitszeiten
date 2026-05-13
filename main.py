from flask import Flask, render_template, url_for, redirect, request, jsonify, session, send_file
from datetime import datetime, date
from models import db, users, token, data, category
import os
from api import app as api_app
from login import change_password, change_username, check_username, checkuser, delete_account, loginChecker, validTokenChecker, logoutUser, checkRegistration, hash_pw
import secrets
from constants import USERID, TOKEN
from time import time
from sqlalchemy import func, distinct
from decimal import Decimal, InvalidOperation

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


def get_effective_maxhours_for_month(user_id, target_date):
    first_of_month = get_month_start(target_date)
    return db.session.query(data.maxhours).filter(
        data.userid == user_id,
        data.date <= first_of_month,
        data.maxhours.isnot(None)
    ).order_by(data.date.desc()).limit(1).scalar()


def get_previous_effective_maxhours(user_id, target_date):
    first_of_month = get_month_start(target_date)
    return db.session.query(data.maxhours).filter(
        data.userid == user_id,
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


def build_home_context(user_id, selected_date):
    german_months = {
        1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
        5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
    }

    selected_date_str = selected_date.isoformat()
    selected_date_display = 'Heute' if selected_date == date.today() else selected_date.strftime('%d.%m.%Y')

    day_total_hours = db.session.query(func.sum(data.data)).filter(
        data.userid == user_id,
        data.date == selected_date
    ).scalar() or Decimal('0')

    month_hours_decimal = db.session.query(func.sum(data.data)).filter(
        data.userid == user_id,
        func.extract('month', data.date) == selected_date.month,
        func.extract('year', data.date) == selected_date.year
    ).scalar() or Decimal('0')

    current_max_hours = get_effective_maxhours_for_month(user_id, selected_date)
    current_max_hours_display = format_decimal_hours(current_max_hours) if current_max_hours is not None else None
    suggested_max_hours_display = current_max_hours_display or ""

    def calculate_total_deficit():
        earliest_entry = db.session.query(func.min(data.date)).filter(
            data.userid == user_id,
            (data.data.isnot(None) | data.maxhours.isnot(None))
        ).scalar()

        if earliest_entry is None:
            return Decimal('0')

        total_deficit = Decimal('0')
        current_month = earliest_entry.replace(day=1)
        end_month = date.today().replace(day=1)

        while current_month <= end_month:
            current_maxhours = get_effective_maxhours_for_month(user_id, current_month)

            if current_maxhours is not None:
                month_actual_hours = db.session.query(func.sum(data.data)).filter(
                    data.userid == user_id,
                    func.extract('year', data.date) == current_month.year,
                    func.extract('month', data.date) == current_month.month
                ).scalar() or Decimal('0')

                total_deficit += month_actual_hours - current_maxhours

            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)

        return total_deficit

    def create_overview_data():
        earliest_entry = db.session.query(func.min(data.date)).filter(
            data.userid == user_id,
            (data.data.isnot(None) | data.maxhours.isnot(None))
        ).scalar()

        if earliest_entry is None:
            return {}

        all_entries = db.session.query(data).filter(
            data.userid == user_id,
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

            month_maxhours = get_effective_maxhours_for_month(user_id, current_month)
            month_total = db.session.query(func.sum(data.data)).filter(
                data.userid == user_id,
                func.extract('year', data.date) == year,
                func.extract('month', data.date) == month
            ).scalar() or Decimal('0')

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

            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)

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
        'total_hours': format_total_hours_with_sign(total_deficit),
        'total_hours_numeric': float(total_deficit),
        'month_hours': format_decimal_hours(month_hours_decimal),
        'month_hours_numeric': float(month_hours_decimal),
        'overview_data': overview_data,
    }


def build_home_json_state(home_context):
    return {
        'selected_date': home_context['selected_date'],
        'selected_date_display': home_context['selected_date_display'],
        'selected_month_name': home_context['selected_month_name'],
        'edit_time': home_context['edit_time'],
        'edit_time_24h': home_context['edit_time_24h'],
        'current_max_hours_display': home_context['current_max_hours_display'],
        'current_max_hours_numeric': home_context['current_max_hours_numeric'],
        'suggested_max_hours_display': home_context['suggested_max_hours_display'],
        'total_hours': home_context['total_hours'],
        'total_hours_numeric': home_context['total_hours_numeric'],
        'month_hours': home_context['month_hours'],
        'month_hours_numeric': home_context['month_hours_numeric'],
        'day_total_hours': float(home_context['day_total_hours']),
        'overview_data': serialize_overview_data(home_context['overview_data']),
    }

db.init_app(app)

with app.app_context():
    db.create_all()

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
            session[USERID] = db.session.query(users).filter(users.username==username).first().id #save in session[] currentUserId
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
            return redirect("/login")
    return render_template('register.html')

@app.route('/home', methods=["GET", "POST"])
@validTokenChecker
def home():
    user_id = session.get(USERID)
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
                    data.userid == user_id,
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
                        userid=user_id,
                        date=first_of_month,
                        categoryid=None,
                        data=None,
                        maxhours=stored_max_hours
                    ))

            elif action in ['add_30', 'sub_30']:
                current_entry = db.session.query(data).filter(
                    data.userid == user_id,
                    data.date == selected_date
                ).first()
                current_total = current_entry.data if current_entry and current_entry.data is not None else Decimal('0')
                current_maxhours = current_entry.maxhours if current_entry else None

                new_total = current_total + Decimal('0.5') if action == 'add_30' else max(Decimal('0'), current_total - Decimal('0.5'))

                db.session.query(data).filter(
                    data.userid == user_id,
                    data.date == selected_date
                ).delete()

                if new_total > 0 or current_maxhours is not None:
                    db.session.add(data(
                        userid=user_id,
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
                            data.userid == user_id,
                            data.date == selected_date
                        ).first()
                        current_maxhours = current_entry.maxhours if current_entry else None

                        db.session.query(data).filter(
                            data.userid == user_id,
                            data.date == selected_date
                        ).delete()

                        if decimal_hours > 0 or current_maxhours is not None:
                            db.session.add(data(
                                userid=user_id,
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

        home_context = build_home_context(user_id, selected_date)
        if wants_json:
            return jsonify(build_home_json_state(home_context))
        return redirect(f"/home?date={home_context['selected_date']}")

    selected_date = parse_selected_date(request.args.get('date', ''))
    home_context = build_home_context(user_id, selected_date)

    if wants_json:
        return jsonify(build_home_json_state(home_context))

    return render_template(
        'home.html',
        user_id=user_id,
        get_username=get_username,
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
        edit_time_24h=home_context['edit_time_24h']
    )

@app.route('/edit')
@validTokenChecker
def edit():
    return render_template('edit.html', user_id=session.get(USERID), get_username=get_username)

@app.route('/profile', methods=["GET", "POST"])
@validTokenChecker
def profile():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "change-username":
            result = change_username(request.form.get("new_username"))

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
    return render_template('profile.html', user_id=session.get(USERID), get_username=get_username)

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
        count = db.session.query(func.count(distinct(data.date))).filter(data.userid == user.id).scalar()
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
