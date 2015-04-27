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
    dtstart = datetime(today.year - 1, today.month - 3, 1)

    quarters = rrule(
        MONTHLY,
        bymonth=(1, 4, 7, 10),
        dtstart=dtstart,
        count=5
    )
    # Omit last quarter in list as it is the current quarter (incomplete).
    return quarters.between(after=dtstart, before=datetime.today())[:-1]


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
