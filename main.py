from flask import Flask, render_template, url_for, redirect, request, jsonify, session, send_file
from models import db, users, token, data, category
import os
from api import app as api_app
from login import change_password, change_username, check_username, checkuser, delete_account, loginChecker, validTokenChecker, logoutUser, checkRegistration, hash_pw
import secrets
from constants import USERID, TOKEN
from time import time
from sqlalchemy import func, distinct

with open(".env", "r") as f:
    for line in f.readlines():
        if line.strip() and not line.strip().startswith("#"):
            attr, val = line.lstrip().split("=", 1)
            os.environ[attr] = val.rstrip("\n")

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
    SECRET_KEY = os.urandom(40),
    SESSION_COOKIE_SECURE = False,
    SESSION_COOKIE_SAMESITE = "Strict"
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

db.init_app(app)

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
    from datetime import datetime, date
    from decimal import Decimal
    
    user_id = session.get(USERID)
    
    # Helper function to get maxhours for a specific month
    def get_maxhours_for_month(target_date):
        """
        Get maxhours for a specific month by looking for the latest maxhours
        entry on or before the target month (stored on 1st of each month)
        """
        # Look for maxhours entry on 1st of target month
        first_of_target_month = target_date.replace(day=1)
        
        current_maxhours = db.session.query(data.maxhours).filter(
            data.userid == user_id,
            data.date == first_of_target_month,
            data.maxhours.isnot(None)
        ).scalar()
        
        if current_maxhours:
            return current_maxhours
        
        # If not found, look backwards month by month until we find maxhours
        current_date = first_of_target_month
        for _ in range(12):  # Limit search to 12 months back
            # Go to previous month
            if current_date.month == 1:
                current_date = current_date.replace(year=current_date.year - 1, month=12)
            else:
                current_date = current_date.replace(month=current_date.month - 1)
            
            prev_maxhours = db.session.query(data.maxhours).filter(
                data.userid == user_id,
                data.date == current_date,
                data.maxhours.isnot(None)
            ).scalar()
            
            if prev_maxhours:
                return prev_maxhours
        
        return None
    
    # Handle +30min/-30min actions and max hours setting
    if request.method == "POST":
        action = request.form.get('action')
        selected_date_str = request.form.get('selected_date')
        
        if action == 'set_max_hours' and selected_date_str:
            max_hours_str = request.form.get('max_hours', '').replace(',', '.')
            try:
                selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                max_hours = Decimal(max_hours_str) if max_hours_str else None
                
                # Always store maxhours on the 1st of the month
                first_of_month = selected_date.replace(day=1)
                
                # Check if entry exists for 1st of the month
                existing_entry = db.session.query(data).filter(
                    data.userid == user_id,
                    data.date == first_of_month
                ).first()
                
                if existing_entry:
                    existing_entry.maxhours = max_hours
                else:
                    # Create new entry with maxhours on 1st of month
                    new_entry = data(
                        userid=user_id,
                        date=first_of_month,
                        categoryid=None,
                        data=None,  # No hours worked on this date
                        maxhours=max_hours
                    )
                    db.session.add(new_entry)
                
                db.session.commit()
                return redirect(f"/home?date={selected_date_str}")
                
            except (ValueError, Exception) as e:
                print(f"Error setting max hours: {e}")
                db.session.rollback()
        
        elif action and selected_date_str and action in ['add_30', 'sub_30']:
            try:
                selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                
                # Get current entry for the date (including maxhours)
                current_entry = db.session.query(data).filter(
                    data.userid == user_id,
                    data.date == selected_date
                ).first()
                
                current_total = current_entry.data if current_entry and current_entry.data else Decimal('0')
                current_maxhours = current_entry.maxhours if current_entry else None
                
                # Calculate new total
                if action == 'add_30':
                    new_total = current_total + Decimal('0.5')
                elif action == 'sub_30':
                    new_total = max(Decimal('0'), current_total - Decimal('0.5'))
                else:
                    new_total = current_total
                
                # Delete existing entries for this date
                db.session.query(data).filter(
                    data.userid == user_id,
                    data.date == selected_date
                ).delete()
                
                # Add new entry if either hours > 0 OR maxhours is set
                if new_total > 0 or current_maxhours is not None:
                    new_entry = data(
                        userid=user_id,
                        date=selected_date,
                        categoryid=None,  # You might want to use a default category
                        data=new_total if new_total > 0 else None,
                        maxhours=current_maxhours
                    )
                    db.session.add(new_entry)
                
                db.session.commit()
                
                # Redirect to avoid form resubmission
                return redirect(f"/home?date={selected_date_str}")
                
            except (ValueError, Exception) as e:
                print(f"Error processing time adjustment: {e}")
                db.session.rollback()

        elif action == 'set_time' and selected_date_str:
            try:
                selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                time_value = request.form.get('time_value')
                
                if time_value:
                    # Parse time value (HH:MM format)
                    time_parts = time_value.split(':')
                    if len(time_parts) == 2:
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1])
                        
                        # Convert to decimal hours
                        decimal_hours = Decimal(hours) + Decimal(minutes) / Decimal(60)
                        
                        # Get current maxhours to preserve it
                        current_entry = db.session.query(data).filter(
                            data.userid == user_id,
                            data.date == selected_date
                        ).first()
                        current_maxhours = current_entry.maxhours if current_entry else None
                        
                        # Delete existing entries for this date
                        db.session.query(data).filter(
                            data.userid == user_id,
                            data.date == selected_date
                        ).delete()
                        
                        # Add new entry if either hours > 0 OR maxhours is set
                        if decimal_hours > 0 or current_maxhours is not None:
                            new_entry = data(
                                userid=user_id,
                                date=selected_date,
                                categoryid=None,
                                data=decimal_hours if decimal_hours > 0 else None,
                                maxhours=current_maxhours
                            )
                            db.session.add(new_entry)
                        
                        db.session.commit()
                        
                        # Redirect to avoid form resubmission
                        return redirect(f"/home?date={selected_date_str}")
                        
            except (ValueError, Exception) as e:
                print(f"Error setting time: {e}")
                db.session.rollback()
    
    # Get the selected date from query parameter or use today as default
    selected_date_str = request.args.get('date', '')
    selected_date = None
    selected_date_display = 'Heute'
    
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            # Check if the selected date is today
            if selected_date == date.today():
                selected_date_display = 'Heute'
            else:
                # Format the date in German format (DD.MM.YYYY)
                selected_date_display = selected_date.strftime('%d.%m.%Y')
        except ValueError:
            # If date parsing fails, use today
            selected_date = date.today()
            selected_date_str = selected_date.isoformat()
    else:
        # Default to today
        selected_date = date.today()
        selected_date_str = selected_date.isoformat()
    
    # Calculate hours for selected date
    day_total_hours = db.session.query(func.sum(data.data)).filter(
        data.userid == user_id,
        data.date == selected_date
    ).scalar() or Decimal('0')
    
    # Format hours for display (e.g., 8.5 -> "8:30")
    def format_hours(decimal_hours):
        if decimal_hours == 0:
            return "0:00"
        hours = int(decimal_hours)
        minutes = int((decimal_hours - hours) * 60)
        return f"{hours}:{minutes:02d}"
    
    edit_time = format_hours(day_total_hours)
    
    # Format time for HTML time input (24-hour format HH:MM)
    def format_time_24h(decimal_hours):
        if decimal_hours == 0:
            return "00:00"
        hours = int(decimal_hours)
        minutes = int((decimal_hours - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"
    
    edit_time_24h = format_time_24h(day_total_hours)
    
    # Calculate cumulative deficit/surplus across all months
    def calculate_total_deficit():
        # Get the earliest entry date to determine the start of calculations
        earliest_entry = db.session.query(func.min(data.date)).filter(
            data.userid == user_id,
            (data.data.isnot(None) | data.maxhours.isnot(None))
        ).scalar()
        
        if earliest_entry is None:
            return Decimal('0')
        
        # Get current date to determine the end of calculations
        current_date = date.today()
        
        total_deficit = Decimal('0')
        
        # Iterate through all months from earliest entry to current month
        current_month = earliest_entry.replace(day=1)
        end_month = current_date.replace(day=1)
        
        while current_month <= end_month:
            # Get maxhours for this month using our helper function
            current_maxhours = get_maxhours_for_month(current_month)
            
            # Only calculate deficit if we have maxhours
            if current_maxhours is not None:
                # Get sum of actual hours for this month
                month_actual_hours = db.session.query(func.sum(data.data)).filter(
                    data.userid == user_id,
                    func.extract('year', data.date) == current_month.year,
                    func.extract('month', data.date) == current_month.month
                ).scalar() or Decimal('0')
                
                # Calculate deficit: actual - maxhours (negative = deficit, positive = surplus)
                month_deficit = month_actual_hours - current_maxhours
                total_deficit += month_deficit
            
            # Move to next month
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)
        
        return total_deficit
    
    total_deficit = calculate_total_deficit()
    
    # Calculate month hours (for the selected date's month)
    month_hours_decimal = db.session.query(func.sum(data.data)).filter(
        data.userid == user_id,
        func.extract('month', data.date) == selected_date.month,
        func.extract('year', data.date) == selected_date.year
    ).scalar() or Decimal('0')
    
    # Get German month name
    german_months = {
        1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
        5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
    }
    selected_month_name = german_months[selected_date.month]
    
    # Get current maxhours for the selected month using new logic
    current_max_hours = get_maxhours_for_month(selected_date)
    
    # Get suggested maxhours for modal (current value or last known value)
    suggested_max_hours = current_max_hours
    
    # Format decimal hours for display (e.g., 3.5 -> "3,5", 4.0 -> "4")
    def format_decimal_hours(decimal_hours):
        if decimal_hours == int(decimal_hours):
            return str(int(decimal_hours))
        else:
            return str(float(decimal_hours)).replace('.', ',')
    
    # Format total hours with sign (e.g., 3.5 -> "+3,5", -2.0 -> "-2", 0 -> "0")
    def format_total_hours_with_sign(decimal_hours):
        if decimal_hours == 0:
            return "0"
        elif decimal_hours > 0:
            if decimal_hours == int(decimal_hours):
                return f"+{int(decimal_hours)}"
            else:
                return f"+{float(decimal_hours)}".replace('.', ',')
        else:  # negative
            if decimal_hours == int(decimal_hours):
                return str(int(decimal_hours))
            else:
                return str(float(decimal_hours)).replace('.', ',')
    
    # Create overview data for total hours modal
    def create_overview_data():
        # Get the earliest entry date to determine the start of overview
        earliest_entry = db.session.query(func.min(data.date)).filter(
            data.userid == user_id,
            (data.data.isnot(None) | data.maxhours.isnot(None))
        ).scalar()
        
        if earliest_entry is None:
            return {}
        
        # Get all actual data entries for user (including entries with only maxhours), ordered by date desc
        all_entries = db.session.query(data).filter(
            data.userid == user_id,
            (data.data.isnot(None) | data.maxhours.isnot(None))
        ).order_by(data.date.desc()).all()
        
        overview_data = {}
        german_months = {
            1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
            5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
        }
        
        # Get current date to determine the end of overview
        current_date = date.today()
        
        # First, create overview data for all months from earliest to current
        current_month = earliest_entry.replace(day=1)
        end_month = current_date.replace(day=1)
        
        while current_month <= end_month:
            year = current_month.year
            month = current_month.month
            month_name = german_months[month]
            
            if year not in overview_data:
                overview_data[year] = {}
            
            if month not in overview_data[year]:
                overview_data[year][month] = {}
            # Get maxhours for this month using our helper function
            month_maxhours = get_maxhours_for_month(current_month)
            
            # Calculate total hours for this month
            month_total = db.session.query(func.sum(data.data)).filter(
                data.userid == user_id,
                func.extract('year', data.date) == year,
                func.extract('month', data.date) == month
            ).scalar() or Decimal('0')
            
            # Calculate surplus/deficit for month
            month_difference = None
            if month_maxhours:
                month_difference = month_total - month_maxhours
            
            overview_data[year][month] = {
                'name': month_name,
                'total_hours': month_total,
                'max_hours': month_maxhours,
                'difference': month_difference,
                'entries': []
            }
            
            # Move to next month
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)
        
        # Now add the actual entries to their respective months
        for entry in all_entries:
            year = entry.date.year
            month = entry.date.month
            
            # Add entry if it has actual hours worked and the month exists in overview_data
            if entry.data and entry.data > 0 and year in overview_data and month in overview_data[year]:
                overview_data[year][month]['entries'].append({
                    'date': entry.date,
                    'hours': entry.data
                })
        
        return overview_data
    
    overview_data = create_overview_data()
    
    return render_template('home.html', 
                         user_id=user_id, 
                         get_username=get_username,
                         selected_date=selected_date_str,
                         selected_date_display=selected_date_display,
                         selected_month_name=selected_month_name,
                         current_max_hours=str(float(current_max_hours)).replace('.', ',') if current_max_hours else None,
                         current_max_hours_numeric=float(current_max_hours) if current_max_hours else 0,
                         suggested_max_hours=str(float(suggested_max_hours)).replace('.', ',') if suggested_max_hours else "",
                         total_hours=format_total_hours_with_sign(total_deficit),
                         total_hours_numeric=float(total_deficit),
                         month_hours=format_decimal_hours(month_hours_decimal),
                         month_hours_numeric=float(month_hours_decimal),
                         overview_data=overview_data,
                         edit_time=edit_time,
                         edit_time_24h=edit_time_24h
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
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080, debug=os.environ.get("debug", False) == "True")
