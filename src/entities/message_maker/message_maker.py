import datetime as dt
import src.utils.tg.piece as piece
piece = piece

from typing import Optional, List

from src.domain.locator import LocatorStorage, Locator
from src.entities.commands_manager.commands import global_command_list, CommandDescription
from src.entities.destination.destination import Destination
from src.entities.destination.settings import DestinationSettings
from src.entities.event.event import Event
from src.utils.tg.tg_emoji import Emoji, get_emoji
from src.entities.message_maker.help import *
from src.utils.tg.piece import P, Pieces
from src.entities.timesheet.timesheet import Timesheet
from src.utils.utils import reduce_list, insert_between

class MessageMaker(LocatorStorage):
  def __init__(self, locator: Locator):
    super().__init__(locator)

  @staticmethod
  def help() -> Pieces:
    return (help_head + '\n\n' + reduce_list(
      lambda a, b: a + b,
      insert_between(
        [P(f'{Emoji.COMMAND} ' + com.preview + '\n' + com.long)
         for com in global_command_list
         if com.addToMenu],
        P('\n\n')
      ),
      P()
    ) +'\n\n' + help_tail)
  
  @staticmethod
  def destinationSets(
    sets: Optional[DestinationSettings],
    command: str,
    include_black_lists: bool = True,
  ) -> Pieces:
    pieces = P(f'{get_emoji("info")} /set_{command}_head Заголовок \n')
    if sets.head is None:
      pieces += 'Его нет :(\n\n'
    else:
      pieces += MessageMaker.delimeter() + '\n'
      pieces += sets.head + '\n\n'

    pieces += f'{get_emoji("info")} /set_{command}_tail Подвал \n'
    if sets.tail is None:
      pieces += 'Его нет :(\n\n'
    else:
      pieces += MessageMaker.delimeter() + '\n'
      pieces += sets.tail + '\n\n'

    if include_black_lists:
      pieces += f'{get_emoji("info")} /set_{command}_black_list Чёрный список событий\n'
      if len(sets.blackList) == 0:
        pieces += 'Пусто!\n\n'
      else:
        pieces += MessageMaker.delimeter() + '\n'
        pieces += P(', '.join([str(n) for n in sets.blackList]) + '\n\n', types='code')

      pieces += f'{get_emoji("info")} /set_{command}_words_black_list Чёрный список слов\n'
      if len(sets.wordsBlackList) == 0:
        pieces += 'Пусто!\n\n'
      else:
        pieces += MessageMaker.delimeter() + '\n'
        pieces += P(', '.join(sets.wordsBlackList) + '\n\n', types='code')
      
    pieces += f'{get_emoji("info")} /set_{command}_event_format Формат строки мероприятия\n'
    if sets.lineFormat is None:
      pieces += 'Обыкновенный'
    else:
      pieces += MessageMaker.delimeter() + '\n'
      pieces += P(sets.lineFormat, types='code')

    return pieces

  @staticmethod
  def timesheet(timesheet: Optional[Timesheet]) -> Pieces:
    pieces = P(f'{get_emoji("infoglob")} О расписании\n')
    if timesheet is None:
      return pieces + 'Его нет\n\n'
    return (pieces +
      f'\n{get_emoji("info")} /set_timesheet Название и пароль\n' +
      MessageMaker.delimeter() + '\n' +
      P('Логин:  ' + timesheet.name, types='code') + '\n' +
      P('Пароль: ' + timesheet.password, types='code') + '\n\n' +
      MessageMaker.destinationSets(timesheet.destinationSets,
                                   include_black_lists=False,
                                   command='timesheet'))

  @staticmethod
  def destination(destination: Optional[Destination]) -> Pieces:
    pieces = P(f'{get_emoji("infoglob")} О подключении\n')
    if destination is None:
      return pieces + 'Его нет\n\n'
    return (pieces +
            f'\n{get_emoji("info")} /set_destination Ссыль\n' +
            MessageMaker.delimeter() + '\n' +
            destination.getUrl() + '\n\n' +
            MessageMaker.destinationSets(destination.sets,
                                         command='destination'))

  @staticmethod
  def timesheetPost(
    events: [Event],
    sets: DestinationSettings,
    randomTimesheet: bool = False,
  ) -> Optional[Pieces]:
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
        paragraph = P(get_day(event.start))
        new_day = False
      if len(paragraph.pieces) > 0:
        paragraph += '\n'
      paragraph += get_event_line(sets.lineFormat or sets.default().lineFormat,
                                  event,
                                  url=event.url,
                                  randomTimesheet=randomTimesheet)
      if i+1 == len(events) or is_other_day(events[i].start, events[i+1].start):
        paragraphs.append(paragraph)
        new_day = True
    if sets.tail is not None:
      paragraphs.append(sets.tail)
    return reduce_list(lambda a, b: a + b, insert_between(paragraphs, '\n\n'), P())
  
  @staticmethod
  def eventPreview(event: Event) -> str:
    line = get_event_line('👉 #%i %s %p %n', event).toString()
    return f'{line}, {event.url}' if event.url is not None else line
  
  @staticmethod
  def eventFormatInput(current_sets: Optional[DestinationSettings]) -> Pieces:
    return (P('Введите формат строки мероприятия\n') +
            P('%s', types='code') + ' - время начала мероприятия\n' +
            P('%p', types='code') + ' - место проведения мероприятия\n' +
            P('%n', types='code') + ' - название мероприятия\n' +
            P('%i', types='code') + ' - идентификатор мероприятия\n' +
            '\nСтандартное значение: ' +
            P(DestinationSettings.default().lineFormat, types='code') +
            '\nТекущее значение: ' +
            (P(current_sets.lineFormat, types='code')
             if current_sets.lineFormat is not None else
             'Отсутствует'))
  
  @staticmethod
  def pageWithCommands(commands: List[CommandDescription]) -> Pieces:
    return P('\n\n'.join([
      f'{Emoji.COMMAND} {command.preview} {command.short}\n'
        + MessageMaker.delimeter()
        + f'\n{command.long}'
      for command in commands
    ]))
  
  @staticmethod
  def delimeter():
    return '═' * 25


def get_event_line(
  fmt: str,
  event: Event,
  url: str = None,
  nested: bool = False,
  randomTimesheet: bool = False,
) -> Optional[Pieces]:
  result = P()
  p, i = 0, 0
  while True:
    i = fmt.find('%', p)
    if i < 0 or i-1 >= len(fmt):
      result += fmt[p:]
      break
    result += fmt[p:i]
    if fmt[i+1] == '%':
      result += fmt[i]
    elif fmt[i+1] == 'p':
      result += event.place.name
    elif fmt[i+1] == 's':
      result += event.start.strftime("%H:%M")
    elif fmt[i+1] == 'n':
      if url is not None and '2139685032' in url and not randomTimesheet:
        result += P(event.desc, url='https://t.me/+mv3RyTBitF1iOWJi')
      else:
        result += P(event.desc, url=url)
    elif fmt[i+1] == 'i':
      result += str(event.id)
    elif fmt[i+1] == 'c':
      if (event.creator is None or
          event.url is not None or
          not isinstance(event.creator, str)) and nested:
        return None
      result += str(event.creator)
    elif fmt[i+1] == 'o':
      if (event.place.org is None or event.place.org == event.place.name) and nested:
        return None
      result += event.place.org
    elif fmt[i+1] == '(':
      nested_result = get_event_line(fmt[i+2:], event, url, True)
      if nested_result is not None:
        result += nested_result
      i = fmt.find('%)', p)
    elif fmt[i+1] == ')' and nested:
      return result
    else:
      result += fmt[i:i+2]
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
  