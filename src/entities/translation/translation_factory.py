from typing import Any, Callable

from telebot import TeleBot

from src.entities.message_maker.message_maker import MessageMaker
from src.entities.timesheet.timesheet_repository import TimesheetRepository
from src.entities.translation.translation import Translation
from src.utils.lira import Lira


class TranslationFactory:
  def __init__(
    self,
    tg: TeleBot,
    timesheet_repo: TimesheetRepository,
    message_maker: MessageMaker,
    lira: Lira,
  ):
    self.tg = tg
    self.timesheetRepo = timesheet_repo
    self.msgMaker = message_maker
    self.lira = lira
    
  def make(
    self,
    event_predicat: Callable = None,
    chat_id: int = None,
    message_id: int = None,
    timesheet_id: int = None,
    id: int = None,
    serialized: {str: Any} = None,
  ) -> Translation:
    if serialized is None:
      id = self.lira.get('translation_counter', 0)
      id += 1
      self.lira.put(id, id='translation_counter', cat='id_counter')
      self.lira.flush()
    return Translation(
      tg=self.tg,
      timesheet_repo=self.timesheetRepo,
      message_maker=self.msgMaker,
      id=id,
      event_predicat=event_predicat,
      chat_id=chat_id,
      message_id=message_id,
      timesheet_id=timesheet_id,
      serialized=serialized,
    )