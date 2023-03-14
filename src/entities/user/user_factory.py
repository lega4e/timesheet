from typing import Any

from telebot import TeleBot

from src.domain.locator import LocatorStorage, Locator
from src.entities.user.user import User


class UserFactory(LocatorStorage):
  def __init__(self, locator: Locator):
    super().__init__(locator)
    self.tg: TeleBot = self.locator.tg()

  def make(
    self,
    channel: str = None,
    chat: int = None,
    timesheet_id: int = None,
    serialized: {str : Any} = None,
  ) -> User:
    return User(
      locator=self.locator,
      channel=channel,
      chat=chat,
      timesheet_id=timesheet_id,
      serialized=serialized,
    )
