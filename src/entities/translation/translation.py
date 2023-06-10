import traceback
from copy import copy

from typing import Any, Callable, Optional

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException

from src.domain.locator import LocatorStorage, Locator
from src.entities.destination.destination import Destination
from src.entities.destination.destination_repo import DestinationRepo
from src.entities.destination.settings import DestinationSettings
from src.entities.event.event import Event
from src.entities.event.event_fields_parser import datetime_today
from src.utils.tg.send_message import send_message
from src.entities.message_maker.message_maker import MessageMaker
from src.utils.tg.piece import Pieces
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
    destination: Destination = None,
    message_id: int = None,
    timesheet_id: int = None,
    creator: int = None, # user chat id
    event_predicat: Callable = None,
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
    if serialized is not None:
      self.deserialize(serialized)
    else:
      assert(None not in [id, destination, timesheet_id, creator])
      self.id = id
      self.destination = destination
      self.messageId = message_id
      self.timesheetId = timesheet_id
      self.creator = creator
    self._dispose = None

  def serialize(self) -> {str: Any}:
    return {
      'id': self.id,
      'destination_id': self.destination.id,
      'message_id': self.messageId,
      'timesheet_id': self.timesheetId,
      'creator': self.creator,
    }
  
  def deserialize(self, serialized: {str: Any}):
    self.id: int = serialized['id']
    self.messageId: int = serialized['message_id']
    self.timesheetId: int = serialized['timesheet_id']
    self.creator: int = serialized.get('creator')
    self.destination = self.destinationRepo.find(serialized.get('destination_id'))

  def connect(self) -> bool:
    if self.destination is None:
      self.emitDestroy('destination is None')
      return False
    timesheet = self._findAndCheckTimesheet()
    if timesheet is None:
      return False
    self._dispose = (timesheet.addListener(lambda _: self._translate()),
                     self.destination.addListener(lambda _: self._translate()))
    if self.messageId is None:
      message = self._getMessage(timesheet)
      if message is None:
        return False
      try:
        self.messageId = send_message(
          tg=self.tg,
          chat=self.destination.chat,
          text=message,
          disable_web_page_preview=True,
        ).message_id
      except Exception as e:
        self.emitDestroy(f'exception on send message: {e}')
        return False
    return True
  
  def updatePost(self) -> bool:
    timesheet = self._findAndCheckTimesheet()
    if timesheet is None:
      return False
    return self._translate()
    
  def emitDestroy(self, reason: str):
    chat = 'none' if self.destination is None else self.destination.getUrl(self.messageId)
    s = f'Translation Emit Destroy {chat} ({reason})'
    self.locator.flogger().info(s)
    if self._dispose is not None:
      self._dispose[0]()
      self._dispose[1]()
      self._dispose = None
    self.notify(Translation.EMIT_DESTROY)

  def _translate(self) -> bool:
    logger = self.locator.flogger()
    logger_title = 'Translate ' + self.destination.getUrl(message_id=self.messageId)
    timesheet = self._findAndCheckTimesheet()
    if timesheet is None:
      return False
    pieces = self._getMessage(timesheet)
    if pieces is None:
      return False
    try:
      chat = copy(self.destination.chat)
      chat.translateToMessageId = self.messageId
      send_message(
        tg=self.tg,
        chat=chat,
        text=pieces,
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
        self.emitDestroy('message to edit not found')
        return False
      elif 'MESSAGE_ID_INVALID' in str(e):
        logger.info(f'{logger_title} message id invalid')
        self.emitDestroy('MESSAGE_ID_INVALID')
        return False
      elif 'chat not found' in str(e):
        logger.info(f'{logger_title} chat not found')
        self.emitDestroy('chat not found')
        return False
      elif 'bot is not a member' in str(e):
        logger.info(f'{logger_title} bot is not a member')
        self.emitDestroy('bot is not a member')
        return False
      else:
        logger.info(f'{logger_title} fail')
        self.logger.error(traceback.format_exc())
        return False
    
  def _getMessage(self, timesheet: Timesheet) -> Optional[Pieces]:
    events = list(timesheet.events(predicat=self.eventPredicat))
    if len(events) == 0:
      self.emitDestroy('message is None')
      return None
    return self.msgMaker.timesheetPost(
      events,
      DestinationSettings.merge(timesheet.destinationSets, self.destination.sets),
    )
  
  def _getLoggerTitle(self):
    chat = copy(self.destination.chat)
    chat.translateToMessageId = self.messageId
    return f'Translate to {chat.translateToMessageId}'
  
  def findTimesheet(self) -> Optional[Timesheet]:
    return self.timesheetRepo.find(self.timesheetId)
  
  def _findAndCheckTimesheet(self):
    timesheet = self.findTimesheet()
    if timesheet is None:
      self.emitDestroy('timesheet is None')
    return timesheet
  
  @staticmethod
  def _defaultPredicat(event: Event) -> bool:
    return event.start >= datetime_today()