from logging import Logger
from typing import List, Union

from telebot import TeleBot

from src.domain.locator import Locator, LocatorStorage
from src.domain.tg.piece import Pieces, P


class FLogger(LocatorStorage):
  def __init__(
    self,
    locator: Locator,
  ):
    super().__init__(locator)
    self.logger: Logger = self.locator.logger()
    self.tg: TeleBot = self.locator.tg()
    self.chats: List[int] = self.locator.config().loggingDefaultChats()

  def info(self, message, *args, **kwargs):
    self.logger.info(message, *args, **kwargs)

  def error(self, message, *args, **kwargs):
    self.logger.error(message, *args, **kwargs)

  def text(self, m, *args, **kwargs):
    self.info(f'[@{FLogger._usernameIdOrId(m)}] {m.text}', *args, **kwargs)

  def answer(self, chat_id: int, text: str, *args, **kwargs):
    self.info(f'[{chat_id}]\n{text}', *args, **kwargs)
    
  def message(
    self,
    text: Union[str, Pieces],
    chat_id = None,
    **kwargs,
  ):
    if self.tg is None:
      return
    if isinstance(text, str):
      text = P(text)
    text, entities = text.toMessage()
    if text is None:
      return
    for chat in self.chats:
      if chat == chat_id:
        continue
      self.tg.send_message(chat_id=chat,
                           text=text,
                           entities=entities,
                           **kwargs)

  @staticmethod
  def _usernameIdOrId(m):
    return (f'{m.chat.username}|{m.chat.id}'
            if m.chat.username is not None
            else m.chat.id)
