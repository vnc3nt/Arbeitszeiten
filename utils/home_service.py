from datetime import date
from decimal import Decimal
from sqlalchemy import func
from models import db, data, profiles
from translations import get_translation, get_month_name
from utils.formatting import (
    format_decimal_hours, format_hours, format_time_24h,
    format_total_hours_with_sign, get_month_start, get_next_month_start,
    serialize_overview_data,
)
from utils.session_helpers import get_current_language


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


def build_home_context(user_id, selected_date, include_total_hours=True, include_overview=True):
    current_lang = get_current_language()

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
    today_label = get_translation('common.today', current_lang)
    selected_date_display = today_label if selected_date == date.today() else selected_date.strftime('%d.%m.%Y')

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
                'name': get_month_name(month, current_lang),
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
        'selected_month_name': get_month_name(selected_date.month, current_lang),
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
