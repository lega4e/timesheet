from typing import Any, Callable

from telebot import TeleBot
from telebot.types import MessageEntity

from src.entities.message_maker.message_maker import MessageMaker
from src.entities.timesheet.timesheet import Timesheet
from src.entities.timesheet.timesheet_repository import TimesheetRepository
from src.utils.notifier import Notifier


class Translation(Notifier):
  EMIT_DESTROY = 'EMIT_DESTROY'
  
  def __init__(
    self,
    tg: TeleBot,
    timesheet_repo: TimesheetRepository,
    message_maker: MessageMaker,
    id: int,
    event_predicat: Callable = None,
    chat_id: int = None,
    message_id: int = None,
    timesheet_id: int = None,
    serialized: {str: Any} = None,
  ):
    super().__init__()
    self.tg = tg
    self.timesheetRepo = timesheet_repo
    self.msgMaker = message_maker
    self.id = id
    self.eventPredicat = event_predicat or (lambda _: True)
    if serialized is None:
      self.chatId = chat_id
      self.messageId = message_id
      self.timesheetId = timesheet_id
    else:
      self.chatId: int = serialized['chat_id']
      self.messageId: int = serialized['message_id']
      self.timesheetId: int = serialized['timesheet_id']
    self._dispose = None

  def serialize(self) -> {str: Any}:
    return {
      'chat_id': self.chatId,
      'message_id': self.messageId,
      'timesheet_id': self.timesheetId,
    }
  
  def connect(self):
    timesheet = self.timesheetRepo.find(self.timesheetId)
    if timesheet is None:
      self.emitDestroy()
      return
    self._dispose = timesheet.addListener(
      self._translate, event=[None, Timesheet.EVENT_CHANGED]
    )
    if self.messageId is None:
      message, entities = self._getMessage(timesheet)
      self.messageId = self.tg.send_message(
        chat_id=self.chatId,
        text=message,
        entities=entities,
        disable_web_page_preview=True,
      ).message_id
      
  def emitDestroy(self):
    self.notify(Translation.EMIT_DESTROY)

  def dispose(self):
    if self._dispose is not None:
      self._dispose()
    self._dispose = None
    
  def _translate(self, timesheet: Timesheet):
    print('TRANSLATE')
    message, entities = self._getMessage(timesheet)
    if message is None:
      return
    self.tg.edit_message_text(
      chat_id=self.chatId,
      message_id=self.messageId,
      text=message,
      entities=entities,
      disable_web_page_preview=True,
    )
    
  def _getMessage(self, timesheet: Timesheet) -> (str, [MessageEntity]):
    events = list(timesheet.events(predicat=self.eventPredicat))
    if len(events) == 0:
      self.emitDestroy()
      return None, None
    return self.msgMaker.createTimesheetPost(events)
