import traceback
from typing import Any, Callable

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import MessageEntity

from src.entities.message_maker.accessory import send_message
from src.entities.message_maker.message_maker import MessageMaker
from src.entities.message_maker.piece import Piece, piece2string, piece2entities
from src.entities.timesheet.timesheet import Timesheet
from src.entities.timesheet.timesheet_repository import TimesheetRepository
from src.utils.logger.logger import FLogger
from src.utils.notifier import Notifier


class Translation(Notifier):
  EMIT_DESTROY = 'EMIT_DESTROY'
  
  def __init__(
    self,
    tg: TeleBot,
    timesheet_repo: TimesheetRepository,
    message_maker: MessageMaker,
    logger: FLogger,
    id: int = None,
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
    self.logger = logger
    self.eventPredicat = event_predicat or (lambda _: True)
    if serialized is None:
      self.id = id
      self.chatId = chat_id
      self.messageId = message_id
      self.timesheetId = timesheet_id
    else:
      self.id: int = serialized['id']
      self.chatId: int = serialized['chat_id']
      self.messageId: int = serialized['message_id']
      self.timesheetId: int = serialized['timesheet_id']
    self._dispose = None

  def serialize(self) -> {str: Any}:
    return {
      'id': self.id,
      'chat_id': self.chatId,
      'message_id': self.messageId,
      'timesheet_id': self.timesheetId,
    }
  
  def connect(self) -> bool:
    timesheet = self.timesheetRepo.find(self.timesheetId)
    if timesheet is None:
      self.emitDestroy()
      return False
    self._dispose = timesheet.addListener(
      self._translate, event=[None, Timesheet.EVENT_CHANGED]
    )
    if self.messageId is None:
      message = self._getMessage(timesheet)
      if message is None:
        self.emitDestroy()
        return False
      try:
        self.messageId = send_message(
          tg=self.tg,
          chat_id=self.chatId,
          message=message,
          disable_web_page_preview=True,
        ).message_id
      except:
        self.emitDestroy()
        return False
    return True
  
  def updatePost(self) -> bool:
    timesheet = self.timesheetRepo.find(self.timesheetId)
    if timesheet is None:
      return False
    return self._translate(timesheet)
    
  def emitDestroy(self):
    print('(Translation.emitDestroy())')
    self.notify(Translation.EMIT_DESTROY)

  def dispose(self):
    if self._dispose is not None:
      self._dispose()
    self._dispose = None
    
  def _translate(self, timesheet: Timesheet) -> bool:
    print('TRANSLATE')
    pieces = self._getMessage(timesheet)
    if pieces is None:
      return False
    message, entities = piece2string(pieces), piece2entities(pieces)
    if message is None:
      return False
    try:
      self.tg.edit_message_text(
        chat_id=self.chatId,
        message_id=self.messageId,
        text=message,
        entities=entities,
        disable_web_page_preview=True,
      )
      return True
    except ApiTelegramException as e:
      if 'message is not modified' in str(e):
        return True
      elif 'message to edit not found' in str(e):
        self.emitDestroy()
      self.logger.error(traceback.format_exc())
      return False
    
  def _getMessage(self, timesheet: Timesheet) -> [Piece]:
    events = list(timesheet.events(predicat=self.eventPredicat))
    if len(events) == 0:
      print('(Translation._getMessage) -> len(events) == 0 -> emitDestroy')
      self.emitDestroy()
      return None
    return self.msgMaker.timesheetPost(events,
                                       head=timesheet.head,
                                       tail=timesheet.tail)
