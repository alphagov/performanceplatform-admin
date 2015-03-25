from datetime import datetime, time, timedelta, date
from dateutil.relativedelta import relativedelta
import pytz


def to_datetime(a_date):
    return datetime.combine(a_date, time(0)).replace(tzinfo=pytz.UTC)


def a_week_ago():
    return date.today() - timedelta(days=7)


def start_of_month(date):
    return date.replace(day=1)


def a_month_ago():
    return date.today() + relativedelta(months=-1)


def start_of_week(date):
    return date - timedelta(days=date.weekday())
