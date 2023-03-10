from sys import stdout
from telebot import TeleBot

from .logger_stream import LoggerStream


class TelegramLoggerStream(LoggerStream):
  def __init__(self, chats: [int], tg: TeleBot):
    self.chats = chats
    self.tg = tg

  def write(self, report):
    for chat in self.chats:
      self.tg.send_message(chat, report, disable_web_page_preview=True)
    stdout.write(report)
