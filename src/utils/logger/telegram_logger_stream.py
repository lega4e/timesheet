from sys import stdout
from typing import List

from telebot import TeleBot

from src.domain.locator import LocatorStorage, Locator
from src.utils.logger.logger_stream import LoggerStream


class TelegramLoggerStream(LoggerStream, LocatorStorage):
  def __init__(self, locator: Locator):
    LocatorStorage.__init__(self, locator)
    self.chats: List[int] = self.locator.config().loggingDefaultChats()
    self.tg: TeleBot = self.locator.tg()

  def write(self, report):
    for chat in self.chats:
      self.tg.send_message(chat, report, disable_web_page_preview=True)
    stdout.write(report)
