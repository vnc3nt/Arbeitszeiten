from datetime import date


def format_hours_clock(decimal_hours, pad_hours=False):
    """Konvertiert Dezimalstunden in Uhrzeitformat H:MM (z.B. 1.5 -> '1:30', 1.75 -> '1:45')."""
    if decimal_hours is None:
        return ""
    val = float(decimal_hours)
    sign = "-" if val < -1e-9 else ""
    val = abs(val)
    total_minutes = int(round(val * 60))
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if pad_hours:
        return f"{sign}{hours:02d}:{minutes:02d}"
    return f"{sign}{hours}:{minutes:02d}"


def format_decimal_hours(decimal_hours):
    if decimal_hours is None:
        return ""
    return format_hours_clock(decimal_hours)


def decimal_comma_filter(value):
    if value is None:
        return ""
    try:
        return format_hours_clock(value)
    except (ValueError, TypeError):
        return str(value).replace(".", ",")


def format_hours(decimal_hours):
    if decimal_hours is None or decimal_hours == 0:
        return "0:00"
    return format_hours_clock(decimal_hours)


def format_time_24h(decimal_hours):
    if decimal_hours is None or decimal_hours == 0:
        return "00:00"
    return format_hours_clock(decimal_hours, pad_hours=True)


def format_total_hours_with_sign(decimal_hours):
    if decimal_hours is None or decimal_hours == 0:
        return "0:00"
    val = float(decimal_hours)
    if val > 0:
        return f"+{format_hours_clock(val)}"
    return format_hours_clock(val)


def get_month_start(target_date):
    return target_date.replace(day=1)


def get_next_month_start(target_date):
    month_start = get_month_start(target_date)
    if month_start.month == 12:
        return month_start.replace(year=month_start.year + 1, month=1)
    return month_start.replace(month=month_start.month + 1)


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
