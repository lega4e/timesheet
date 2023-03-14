import os


class Locator:
  def __init__(self):
    self._config = None
    self._eventFactory = None
    self._eventRepository = None
    self._flogger = None
    self._lira = None
    self._logger = None
    self._loggerStream = None
    self._messageMaker = None
    self._tg = None
    self._timesheetFactory = None
    self._timesheetRepository = None
    self._translationFactory = None
    self._translationRepo = None
    self._userFactory = None
    self._userRepository = None
    
  def config(self):
    if self._config is None:
      from src.domain.config import Config
      self._config = Config()
    return self._config
  
  def eventFactory(self):
    if self._eventFactory is None:
      from src.entities.event.event_factory import EventFactory
      self._eventFactory = EventFactory(self)
    return self._eventFactory
  
  def eventRepository(self):
    if self._eventRepository is None:
      from src.entities.event.event_repository import EventRepository
      self._eventRepository = EventRepository(self)
    return self._eventRepository
  
  def flogger(self):
    if self._flogger is None:
      from src.utils.logger.logger import FLogger
      self._flogger = FLogger(self)
    return self._flogger
  
  def lira(self):
    if self._lira is None:
      from src.utils.lira import Lira
      os.makedirs('lira', exist_ok=True)
      self._lira = Lira('lira/data.lr', 'lira/head.lr')
    return self._lira
  
  def logger(self):
    if self._logger is None:
      import logging
      logging.basicConfig(
        format=self.config().loggingFormat(),
        datefmt=self.config().loggingDateFormat(),
        stream=self.loggerStream(),
      )
      self._logger = logging.getLogger('global')
      self._logger.setLevel(logging.INFO)
      self._logger.com = lambda com, m: self._logger.info(f'{com} {m.chat.id}')
    return self._logger
  
  def loggerStream(self):
    if self._loggerStream is None:
      from src.utils.logger.telegram_logger_stream import TelegramLoggerStream
      self._loggerStream = TelegramLoggerStream(self)
    return self._loggerStream
  
  def messageMaker(self):
    if self._messageMaker is None:
      from src.entities.message_maker.message_maker import MessageMaker
      self._messageMaker = MessageMaker(self)
    return self._messageMaker
  
  def tg(self):
    if self._tg is None:
      from telebot import TeleBot
      self._tg = TeleBot(token=self.config().token())
    return self._tg
  
  def timesheetFactory(self):
    if self._timesheetFactory is None:
      from src.entities.timesheet.timesheet_factory import TimesheetFactory
      self._timesheetFactory = TimesheetFactory(self)
    return self._timesheetFactory
  
  def timesheetRepo(self):
    if self._timesheetRepository is None:
      from src.entities.timesheet.timesheet_repository import TimesheetRepo
      self._timesheetRepository = TimesheetRepo(self)
    return self._timesheetRepository
  
  def translationFactory(self):
    if self._translationFactory is None:
      from src.entities.translation.translation_factory import TranslationFactory
      self._translationFactory = TranslationFactory(self)
    return self._translationFactory
  
  def translationRepo(self):
    if self._translationRepo is None:
      from src.entities.translation.translation_repository import TranslationRepo
      self._translationRepo = TranslationRepo(self)
    return self._translationRepo
  
  def userFactory(self):
    if self._userFactory is None:
      from src.entities.user.user_factory import UserFactory
      self._userFactory = UserFactory(self)
    return self._userFactory
  
  def userRepo(self):
    if self._userRepository is None:
      from src.entities.user.user_repository import UserRepo
      self._userRepository = UserRepo(self)
    return self._userRepository


class LocatorStorage:
  def __init__(self, locator: Locator = None):
    self.locator = locator or Locator
    
    
_global_locator = Locator()

def glob():
  return _global_locator