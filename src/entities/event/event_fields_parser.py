import datetime as dt
import re


def parse_datetime(text: str) -> (dt.datetime, str):
  formats = [
    '%d %B %Y %H:%M',
    '%d %B %Y %H:%M',
    '%d %B %H:%M',
    '%d %B %H %M',
    '%d.%m %H:%M',
    '%d.%m %H %M'
  ]
  for fmt in formats:
    try:
      return dt.datetime.strptime(text, fmt), None
    except:
      continue
  return (None, 'Не получилось считать дату время :( Введите время в одном из следующих форматов:\n'
                + '\n'.join([dt.datetime.now().strftime(fmt) for fmt in formats]))

def correct_datetime(
  value: dt.datetime,
  isfuture: bool = False,
  delta: dt.timedelta = dt.timedelta()
) -> dt.datetime:
  value = datetime_copy_with(value, dt.datetime.now().year)
  return (datetime_copy_with(value, value.year+1)
          if isfuture and value < dt.datetime.now() - delta else
          value)
  
  
def check_url(text: str):
  return re.match(r'^https?://.*\..+', text) is not None
  
  
def datetime_copy_with(
  val: dt.datetime,
  year: int = None,
  month: int = None,
  day: int = None,
  hour: int = None,
  minute: int = None,
  second: int = None,
  microsecond: int = None
):
    return dt.datetime(year=val.year if year is None else year,
                       month=val.month if month is None else month,
                       day=val.day if day is None else day,
                       hour=val.hour if hour is None else hour,
                       minute=val.minute if minute is None else minute,
                       second=val.second if second is None else second,
                       microsecond=val.microsecond if microsecond is None else
                                   microsecond)


def datetime_today() -> dt.datetime:
  return datetime_copy_with(dt.datetime.now(),
                             hour=0,
                             minute=0,
                             second=0,
                             microsecond=0)
