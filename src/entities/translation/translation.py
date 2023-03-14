import traceback

from typing import Any, Callable

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException

from src.domain.locator import LocatorStorage, Locator, glob
from src.entities.destination.destination import Destination
from src.entities.destination.destination_repo import DestinationRepo
from src.entities.destination.settings import DestinationSettings
from src.entities.event.event import Event
from src.entities.event.event_fields_parser import datetime_today
from src.entities.message_maker.accessory import send_message
from src.entities.message_maker.message_maker import MessageMaker
from src.entities.message_maker.piece import Piece, piece2string, piece2entities
from src.entities.timesheet.timesheet import Timesheet
from src.entities.timesheet.timesheet_repository import TimesheetRepo
from src.utils.logger.logger import FLogger
from src.utils.notifier import Notifier
from src.utils.serialize import Serializable


class Translation(Notifier, LocatorStorage, Serializable):
  EMIT_DESTROY = 'EMIT_DESTROY'
  
  def __init__(
    self,
    locator: Locator,
    id: int = None,
    event_predicat: Callable = None,
    destination_id: int = None,
    message_id: int = None,
    timesheet_id: int = None,
    serialized: {str: Any} = None,
  ):
    Notifier.__init__(self)
    LocatorStorage.__init__(self, locator)
    self.tg: TeleBot = self.locator.tg()
    self.timesheetRepo: TimesheetRepo = self.locator.timesheetRepo()
    self.msgMaker: MessageMaker = self.locator.messageMaker()
    self.logger: FLogger = self.locator.flogger()
    self.eventPredicat = event_predicat or Translation._defaultPredicat
    self.destinationRepo: DestinationRepo = self.locator.destinationRepo()
    self._dispose = None
    if serialized is not None:
      self.deserialize(serialized)
    else:
      self.id = id
      self.destination = self.destinationRepo.find(destination_id)
      self.messageId = message_id
      self.timesheetId = timesheet_id

  def serialize(self) -> {str: Any}:
    return {
      'id': self.id,
      'destination_id': None if self.destination is None else self.destination.id,
      'message_id': self.messageId,
      'timesheet_id': self.timesheetId,
    }
  
  def deserialize(self, serialized: {str: Any}):
    self.id: int = serialized['id']
    self.destination: Destination = self.destinationRepo.find(serialized.get('destination_id'))
    self.messageId: int = serialized['message_id']
    self.timesheetId: int = serialized['timesheet_id']
    chat_id = serialized.get('chat_id')
    if chat_id is not None:
      self.destination = Destination(chat=chat_id)

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
          chat_id=self._destinationChat(),
          text=message,
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
    s = f'Translation Emit Destroy {self._destinationChat()}, {self.messageId}'
    glob().flogger().info(s)
    self.notify(Translation.EMIT_DESTROY)

  def dispose(self):
    if self._dispose is not None:
      self._dispose()
    self._dispose = None
    
  def _translate(self, timesheet: Timesheet) -> bool:
    logger = glob().flogger()
    pieces = self._getMessage(timesheet)
    logger_title = self._getLoggerTitle()
    if pieces is None:
      logger.info(f'{logger_title} no pieces')
      return False
    message, entities = piece2string(pieces), piece2entities(pieces)
    if message is None:
      logger.info(f'{logger_title} message is none')
      return False
    try:
      self.tg.edit_message_text(
        chat_id=self._destinationChat(),
        message_id=self.messageId,
        text=message,
        entities=entities,
        disable_web_page_preview=True,
      )
      logger.info(f'{logger_title} success')
      return True
    except ApiTelegramException as e:
      if 'message is not modified' in str(e):
        logger.info(f'{logger_title} not modified')
        return True
      elif 'message to edit not found' in str(e):
        logger.info(f'{logger_title} message not found')
        self.emitDestroy()
        return False
      elif 'MESSAGE_ID_INVALID' in str(e):
        logger.info(f'{logger_title} message id invalid')
        self.emitDestroy()
        return False
      elif 'chat not found' in str(e):
        logger.info(f'{logger_title} chat not found')
        self.emitDestroy()
        return False
      elif 'bot is not a member' in str(e):
        logger.info(f'{logger_title} bot is not a member')
        self.emitDestroy()
        return False
      else:
        logger.info(f'{logger_title} fail')
        self.logger.error(traceback.format_exc())
        return False
    
  def _getMessage(self, timesheet: Timesheet) -> [Piece]:
    events = list(timesheet.events(predicat=self.eventPredicat))
    if len(events) == 0 or self.destination is None:
      title = self._getLoggerTitle()
      glob().flogger().info(f'{title} len(events) == 0 -> EmitDestroy')
      self.emitDestroy()
      return None
    return self.msgMaker.timesheetPost(
      events,
      DestinationSettings.merge(timesheet.destinationSets, self.destination.sets),
    )
    
  
  def _getLoggerTitle(self):
    if self.destination is None:
      chat_id_str = 'None'
    else:
      chat_id_str = (str(self._destinationChat())
                     if isinstance(self._destinationChat(), int) else
                     self._destinationChat()[1:])
    return f'Translate to t.me/{chat_id_str}/{self.messageId}'
  
  def _destinationChat(self):
    return None if self.destination is None else self.destination.chat
  
  @staticmethod
  def _defaultPredicat(event: Event) -> bool:
    return event.start >= datetime_today()