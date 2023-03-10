import datetime as dt

from telebot.types import MessageEntity

from src.entities.event.event import Event, Place


class Piece:
  def __init__(self, text: str, url: str = None):
    self.text = text
    self.url = url


class MessageMaker:
  def __init__(self):
    pass

  @staticmethod
  def greeting() -> str:
    return 'Приветствую тебя!'

  @staticmethod
  def help() -> str:
    return 'Помощь'

  @staticmethod
  def createTimesheetPost(events: [Event]) -> (str, [MessageEntity]):
    assert(len(events) != 0)
    events = sorted(events, key=lambda e: e.start)
    head = Piece('Общий график мероприятий Энтузиастов Москвы')
    tail = Piece('Плоt t.me/spores_of_kindness\n'
                 'Клуб Джерри Рубина vk.com/jerryrubinclub\n'
                 'Точка t.me/tochka_place\n'
                 'ТОДД t.me/toddmskinfo')
    paragraphs = [[head]]
    paragraph = []
    new_day = True
    for i in range(len(events)):
      event = events[i]
      if new_day:
        paragraph = [Piece(get_day(event.start))]
        new_day = False
      if len(paragraph) > 0:
        paragraph.append(Piece('\n'))
      paragraph.extend(get_event_line(event, url=event.url))
      if i+1 == len(events) or is_other_day(events[i].start, events[i+1].start):
        paragraphs.append(paragraph)
        new_day = True
    paragraphs.append([tail])
    result = [*paragraphs[0]]
    for p in paragraphs[1:]:
      result.extend([Piece('\n\n'), *p])
    return piece2string(result), piece2entities(result)
  
  
def piece2string(pieces: [Piece]) -> str:
  return ''.join([p.text for p in pieces])


def piece2entities(pieces: [Piece]) -> [MessageEntity]:
  # pos += 1 if len(bytes(text[i], encoding='utf-8')) < 4 else 2
  pos = 0
  entities = []
  for piece in pieces:
    if piece.url is not None:
      entities.append(MessageEntity(
        type='text_link',
        offset=pos,
        length=count_chars(piece.text),
        url=piece.url,
      ))
    pos += count_chars(piece.text)
  return entities


def count_chars(text: str) -> int:
  count = 0
  for c in text:
    count += 1 if len(bytes(c, encoding='utf-8')) < 4 else 2
  return count
  
  
def insert_between(values: [], term) -> []:
  if len(values) == 0:
    return values
  result = [values[0]]
  for value in values[1:]:
    result.extend([term, value])
  return result
  
  
def is_other_day(lhs: dt.datetime, rhs: dt.datetime):
  return (dt.datetime(year=lhs.year, month=lhs.month, day=lhs.day) !=
          dt.datetime(year=rhs.year, month=rhs.month, day=rhs.day))
  
  
def get_day(date: dt.datetime) -> str:
  return date.strftime('%d %B, %A')


def get_place(place: Place) -> str:
  return {
    Place.PLOT : 'Плоt',
    Place.TOCHKA : 'То4ка',
    Place.BOILER_HOUSE: 'Котельная',
  }.get(place.name) or place.name


def get_start_finish_time(start: dt.datetime, finish: dt.datetime) -> str:
  return f'{start.strftime("%H:%M")}-{finish.strftime("%H:%M")}'


def get_event_line(event: Event, url: str = None) -> [Piece]:
  return [Piece('👉 ' + get_place(event.place) + ' ' +
                get_start_finish_time(event.start, event.finish) + ' '),
          Piece(event.desc, url=url)]
