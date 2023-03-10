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
  def copy_with(val: dt.datetime, year: int):
    return dt.datetime(year=year,
                       month=val.month,
                       day=val.day,
                       hour=val.hour,
                       minute=val.minute,
                       second=val.second,
                       microsecond=val.microsecond)
  value = copy_with(value, dt.datetime.now().year)
  return (copy_with(value, value.year+1)
          if isfuture and value < dt.datetime.now() - delta else
          value)
  
  
def check_url(text: str):
  return re.match(r'^https?://.*\..+', text) is not None
