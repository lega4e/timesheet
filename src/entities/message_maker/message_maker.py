import datetime as dt
from typing import Optional

from src.domain.locator import LocatorStorage, Locator
from src.entities.commands_manager.commands import global_command_list
from src.entities.destination.destination import Destination
from src.entities.destination.settings import DestinationSettings
from src.entities.event.event import Event
from src.entities.message_maker.emoji import Emoji
from src.entities.message_maker.help import *
from src.entities.message_maker.piece import *
from src.entities.timesheet.timesheet import Timesheet
from src.utils.utils import reduce_list, insert_between


class MessageMaker(LocatorStorage):
  def __init__(self, locator: Locator):
    super().__init__(locator)

  @staticmethod
  def help() -> [Piece]:
    pieces = []
    pieces.extend(help_head)
    pieces.append(Piece('\n\n'))
    pieces.extend(
      reduce_list(lambda a, b: a + b,
                  insert_between(
                    [[Piece(f'{Emoji.COMMAND} ' + com.preview + '\n'), Piece(com.long)]
                     for com in global_command_list],
                    [Piece('\n\n')],
                  ),
                  []),
    )
    pieces.append(Piece('\n\n'))
    pieces.extend(help_tail)
    return pieces
  
  @staticmethod
  def destinationSets(
    sets: Optional[DestinationSettings],
    command: str,
    include_black_lists: bool = True,
  ) -> [Piece]:
    pieces = list()

    pieces.append(Piece(f'{get_emoji("info")} Заголовок /set_{command}_head\n'))
    if sets.head is None:
      pieces.append(Piece(f'Его нет :(\n\n'))
    else:
      pieces.extend([*sets.head, Piece('\n\n')])

    pieces.append(Piece(f'{get_emoji("info")} Подвал /set_{command}_tail\n'))
    if sets.tail is None:
      pieces.append(Piece(f'Его нет :(\n\n'))
    else:
      pieces.extend([*sets.tail, Piece('\n\n')])

    if include_black_lists:
      pieces.append(Piece(f'{get_emoji("info")} Чёрный список событий /set_{command}_black_list\n'))
      if len(sets.blackList) == 0:
        pieces.append(Piece(f'Пусто!\n\n'))
      else:
        pieces.append(Piece(', '.join([str(n) for n in sets.blackList]) + '\n\n', type='code'))

      pieces.append(Piece(f'{get_emoji("info")} Чёрный список слов /set_{command}_words_black_list\n'))
      if len(sets.wordsBlackList) == 0:
        pieces.append(Piece(f'Пусто!\n\n'))
      else:
        pieces.append(Piece(', '.join(sets.wordsBlackList) + '\n\n', type='code'))
      
    pieces.append(Piece(f'{get_emoji("info")} Формат строки мероприятия /set_{command}_event_format\n'))
    if sets.lineFormat is None:
      pieces.append(Piece(f'Обыкновенный'))
    else:
      pieces.append(Piece(sets.lineFormat, type='code'))

    return pieces

  @staticmethod
  def timesheet(timesheet: Optional[Timesheet]) -> [Piece]:
    pieces = list()
    pieces.append(Piece(f'{get_emoji("infoglob")} О расписании\n'))
    if timesheet is None:
      pieces.append(Piece('Его нет\n\n'))
      return pieces
    pieces.append(Piece(f'\n{get_emoji("info")} Название и пароль /set_timesheet\n'))
    pieces.append(Piece(timesheet.name, type='code'))
    pieces.append(Piece('\n'))
    pieces.append(Piece(timesheet.password, type='code'))
    pieces.append(Piece('\n\n'))
    pieces.extend(MessageMaker.destinationSets(timesheet.destinationSets,
                                               include_black_lists=False,
                                               command='timesheet'))
    return pieces

  @staticmethod
  def destination(destination: Optional[Destination]) -> [Piece]:
    pieces = list()
    pieces.append(Piece(f'{get_emoji("infoglob")} О подключении\n'))
    if destination is None:
      pieces.append(Piece('Его нет\n\n'))
      return pieces
    pieces.append(Piece(f'\n{get_emoji("info")} Ссыль /set_destination\n'))
    pieces.append(Piece(f't.me/{MessageMaker.chat(destination.chat)}'))
    pieces.append(Piece('\n\n'))
    pieces.extend(MessageMaker.destinationSets(destination.sets,
                                               command='destination'))
    return pieces
  
  @staticmethod
  def chat(chat) -> str:
    return str(chat) if isinstance(chat, int) else chat[1:]

  @staticmethod
  def timesheetPost(
    events: [Event],
    sets: DestinationSettings,
  ) -> Optional[List[Piece]]:
    events = list(filter(lambda e: event_predicat(e, sets), events))
    if len(events) == 0:
      return None
    events = sorted(events, key=lambda e: e.start)
    paragraphs = []
    if sets.head is not None:
      paragraphs.append(sets.head)
    paragraph = []
    new_day = True
    for i in range(len(events)):
      event = events[i]
      if new_day:
        paragraph = [Piece(get_day(event.start))]
        new_day = False
      if len(paragraph) > 0:
        paragraph.append(Piece('\n'))
      paragraph.extend(get_event_line(sets.lineFormat or sets.default().lineFormat,
                                      event, url=event.url))
      if i+1 == len(events) or is_other_day(events[i].start, events[i+1].start):
        paragraphs.append(paragraph)
        new_day = True
    if sets.tail is not None:
      paragraphs.append(sets.tail)
    result = [*paragraphs[0]]
    for p in paragraphs[1:]:
      result.extend([Piece('\n\n'), *p])
    return result
  
  @staticmethod
  def eventPreview(event: Event) -> str:
    line = ''.join([piece.text for piece in get_event_line('👉 #%i %s %p %n', event)])
    return f'{line}, {event.url}' if event.url is not None else line


def get_event_line(fmt: str, event: Event, url: str = None) -> [Piece]:
  result = []
  p, i = 0, 0
  while True:
    i = fmt.find('%', p)
    if i < 0 or i-1 >= len(fmt):
      result.append(Piece(fmt[p:]))
      break
    result.append(Piece(fmt[p:i]))
    if fmt[i+1] == '%':
      result.append(Piece(fmt[i]))
    elif fmt[i+1] == 'p':
      result.append(Piece(event.place.name))
    elif fmt[i+1] == 's':
      result.append(Piece(event.start.strftime("%H:%M")))
    elif fmt[i + 1] == 'n':
      result.append(Piece(event.desc, url=url))
    elif fmt[i+1] == 'i':
      result.append(Piece(str(event.id)))
    else:
      result.append(Piece(fmt[i:i+2]))
    p = i+2
  return result


def is_other_day(lhs: dt.datetime, rhs: dt.datetime):
  return (dt.datetime(year=lhs.year, month=lhs.month, day=lhs.day) !=
          dt.datetime(year=rhs.year, month=rhs.month, day=rhs.day))
  
  
def get_day(date: dt.datetime, weekday: bool = True) -> str:
  return (str(int(date.strftime('%d'))) + ' '+
          date.strftime('%B') + (', ' + date.strftime('%A')
                                 if weekday else
                                 '')).lower()

def event_predicat(event: Event, sets: DestinationSettings):
  if event.id in sets.blackList:
    return False
  for word in sets.wordsBlackList:
    if word.lower() in event.desc.lower():
      return False
  return True
  