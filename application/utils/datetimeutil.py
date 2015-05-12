from datetime import datetime, time, timedelta, date

from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY

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


def previous_year_quarters():

    today = date.today()
    day = 1
    month = range(1, 13)[(today.month - 1) - 3]
    if month > 9:
        start_year = today.year - 2
        end_year = today.year - 1
    else:
        start_year = today.year - 1
        end_year = today.year
    dtstart = datetime(start_year, month, day)
    dtend = datetime(end_year, month, today.day)

    quarters = rrule(
        MONTHLY,
        bymonth=(1, 4, 7, 10),
        dtstart=dtstart,
        count=5
    )
    return quarters.between(after=dtstart, before=dtend)


def end_of_quarter(date):
    # Placeholder. Undoubtedly there's a better way of doing this.
    if date.month in [1, 2, 3]:
        return datetime(date.year, 3, 31)
    if date.month in [4, 5, 6]:
        return datetime(date.year, 6, 30)
    if date.month in [7, 8, 9]:
        return datetime(date.year, 9, 30)
    if date.month in [10, 11, 12]:
        return datetime(date.year, 12, 31)
