from sys import stdout
from typing import List

from telebot import TeleBot

from src.utils.logger.logger_stream import LoggerStream


class TelegramLoggerStream(LoggerStream):
  def __init__(self, tg: TeleBot, chats: List[int]):
    self.tg = tg
    self.chats = chats

  def write(self, report):
    for chat in self.chats:
      self.tg.send_message(chat, report, disable_web_page_preview=True)
    stdout.write(report)
