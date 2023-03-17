import datetime as dt
import re

from telebot.types import Message

from src.entities.event.event_fields_parser import correct_datetime
from src.utils.utils import reduce_list


class PostParserAnswer:
  def __init__(
    self,
    datetime: dt.datetime = None,
    url: str = None,
  ):
    self.datetime = datetime
    self.url = url
    

def parse_post(m: Message) -> PostParserAnswer:
  answer = PostParserAnswer()
  text = m.text or m.caption
  time = re.search(r'(\d?\d):(\d\d)', text)
  monthes = reduce_list(lambda a, b: a + b, _monthes.values(), [])
  date = re.search(r'(\d?\d) (%s)' % '|'.join(monthes), text)
  if None not in [date, time]:
    try:
      for num, month in _monthes.items():
        if date.group(2) in month:
          answer.datetime = correct_datetime(dt.datetime(year=1900,
                                                         month=num,
                                                         day=int(date.group(1)),
                                                         hour=int(time.group(1)),
                                                         minute=int(time.group(2))))
          break
    except:
      pass
      
  return PostParserAnswer()


_monthes = {
  1: ['янв', 'январь', 'января'],
  2: ['фев', 'февраль', 'февраля'],
  3: ['мар', 'март', 'марта'],
  4: ['апр', 'апрель', 'апреля'],
  5: ['май', 'май', 'мая'],
  6: ['июн', 'июнь', 'июня'],
  7: ['июл', 'июль', 'июля'],
  8: ['авг', 'август', 'августа'],
  9: ['сен', 'сентябрь', 'сентября'],
  10: ['окт', 'октябрь', 'октября'],
  11: ['ноя', 'ноябрь', 'ноября'],
  12: ['дек', 'декабрь', 'декабря'],
}