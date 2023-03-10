from typing import Any

from telebot import TeleBot

from src.entities.event.event_factory import EventFactory
from src.entities.event.event_repository import EventRepository
from src.entities.event.event_tg_maker import EventTgMaker
from src.entities.timesheet.timesheet_repository import TimesheetRepository
from src.entities.translation.translation_factory import TranslationFactory
from src.entities.translation.translation_repository import TranslationRepo
from src.entities.user.user import User
from src.entities.message_maker.message_maker import MessageMaker
from src.utils.logger.logger import FLogger


class UserFactory:
  def __init__(
    self,
    tg: TeleBot,
    msg_maker: MessageMaker,
    event_factory: EventFactory,
    event_repository: EventRepository,
    timesheet_repository: TimesheetRepository,
    translation_factory: TranslationFactory,
    translation_repo: TranslationRepo,
    logger: FLogger,
  ):
    self.tg = tg
    self.msgMaker = msg_maker
    self.eventFactory = event_factory
    self.eventRepository = event_repository
    self.timesheetRepository = timesheet_repository
    self.translationFactory = translation_factory
    self.translationRepo = translation_repo
    self.logger = logger

  def make(
    self,
    channel: str = None,
    chat: int = None,
    timesheet_id: int = None,
    serialized: {str : Any} = None,
  ) -> User:
    return User(
      tg=self.tg,
      msg_maker=self.msgMaker,
      event_repository=self.eventRepository,
      event_factory=self.eventFactory,
      timesheet_repository=self.timesheetRepository,
      translation_factory=self.translationFactory,
      translation_repo=self.translationRepo,
      logger=self.logger,
      channel=channel,
      chat=chat,
      timesheet_id=timesheet_id,
      serialized=serialized,
    )
