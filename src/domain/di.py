import logging
import os

from telebot import TeleBot

from src.domain.config import Config
from src.entities.event.event_factory import EventFactory
from src.entities.event.event_repository import EventRepository
from src.entities.timesheet.timesheet_factory import TimesheetFactory
from src.entities.timesheet.timesheet_repository import TimesheetRepository
from src.entities.translation.translation_factory import TranslationFactory
from src.entities.translation.translation_repository import TranslationRepo
from src.entities.user.user_factory import UserFactory
from src.entities.message_maker.message_maker import MessageMaker
from src.entities.user.user_repository import UserRepository
from src.utils.lira import Lira
from src.utils.logger.logger import FLogger
from src.utils.logger.logger_stream import LoggerStream
from src.utils.logger.telegram_logger_stream import TelegramLoggerStream


class Di:
  def __init__(self):
    self._config = None
    self._flogger = None
    self._eventFactory = None
    self._eventRepository = None
    self._lira = None
    self._logger = None
    self._loggerStream = None
    self._messageMaker = None
    self._timesheetFactory = None
    self._timesheetRepository = None
    self._translationFactory = None
    self._translationRepo = None
    self._tg = None
    self._userFactory = None
    self._userRepository = None

  def config(self) -> Config:
    if self._config is None:
      self._config = Config()
    return self._config

  def flogger(self) -> FLogger:
    if self._flogger is None:
      self._flogger = FLogger(
        logger=self.logger()
      )
    return self._flogger

  def eventFactory(self) -> EventFactory:
    if self._eventFactory is None:
      self._eventFactory = EventFactory(
        lira=self.lira()
      )
    return self._eventFactory

  def eventRepository(self) -> EventRepository:
    if self._eventRepository is None:
      self._eventRepository = EventRepository(
        event_factory=self.eventFactory(),
        lira=self.lira(),
      )
    return self._eventRepository
  
  def lira(self) -> Lira:
    if self._lira is None:
      os.makedirs('lira', exist_ok=True)
      self._lira = Lira('lira/data.lr', 'lira/head.lr')
    return self._lira

  def logger(self) -> logging.Logger:
    if self._logger is None:
      logging.basicConfig(
        format=self.config().loggingFormat(),
        datefmt=self.config().loggingDateFormat(),
        stream=self.logger_stream(),
      )
      self._logger = logging.getLogger('global')
      self._logger.setLevel(logging.INFO)
      self._logger.com = lambda com, m: self._logger.info(f'{com} {m.chat.id}')
    return self._logger

  def logger_stream(self) -> LoggerStream:
    if self._loggerStream is None:
      self._loggerStream = TelegramLoggerStream(
        chats=self.config().loggingDefaultChats(),
        tg=self.tg(),
      )
    return self._loggerStream

  def message_maker(self) -> MessageMaker:
    if self._messageMaker is None:
      self._messageMaker = MessageMaker()
    return self._messageMaker

  def timesheetFactory(self) -> TimesheetFactory:
    if self._timesheetFactory is None:
      self._timesheetFactory = TimesheetFactory(
        lira=self.lira(),
        event_repository=self.eventRepository(),
      )
    return self._timesheetFactory

  def timesheetRepository(self) -> TimesheetRepository:
    if self._timesheetRepository is None:
      self._timesheetRepository = TimesheetRepository(
        timesheet_factory=self.timesheetFactory(),
        lira=self.lira(),
      )
    return self._timesheetRepository

  def translationFactory(self) -> TranslationFactory:
    if self._translationFactory is None:
      self._translationFactory = TranslationFactory(
        tg=self.tg(),
        timesheet_repo=self.timesheetRepository(),
        message_maker=self.message_maker(),
        lira=self.lira(),
      )
    return self._translationFactory
  
  def translationRepo(self) -> TranslationRepo:
    if self._translationRepo is None:
      self._translationRepo = TranslationRepo(
        translation_factory=self.translationFactory(),
        lira=self.lira(),
      )
    return self._translationRepo

  def tg(self) -> TeleBot:
    if self._tg is None:
      self._tg = TeleBot(token=self.config().token())
    return self._tg

  def userFactory(self) -> UserFactory:
    if self._userFactory is None:
      self._userFactory = UserFactory(
        tg=self.tg(),
        msg_maker=self.message_maker(),
        event_factory=self.eventFactory(),
        event_repository=self.eventRepository(),
        timesheet_repository=self.timesheetRepository(),
        translation_factory=self.translationFactory(),
        translation_repo=self.translationRepo(),
        logger=self.flogger(),
      )
    return self._userFactory

  def userRepository(self) -> UserRepository:
    if self._userRepository is None:
      self._userRepository = UserRepository(
        user_factory=self.userFactory(),
        lira=self.lira(),
      )
    return self._userRepository


_di = Di()


def glob() -> Di:
  return _di
