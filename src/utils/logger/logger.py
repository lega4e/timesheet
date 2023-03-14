from logging import Logger
from typing import List, Union

from telebot import TeleBot

from src.domain.locator import Locator, LocatorStorage
from src.entities.message_maker.piece import Piece, piece2message


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
    pieces: Union[str, List[Piece]],
    chat_id = None,
    entities = None,
    emoji: str = None,
    **kwargs,
  ):
    if self.tg is None:
      return
    for chat in self.chats:
      if chat == chat_id:
        continue
      if entities is None:
        message, ent = piece2message(pieces, emoji=emoji)
      else:
        message, ent = pieces, entities
      if message is not None:
        self.tg.send_message(chat_id=chat, text=message, entities=ent, **kwargs)

  @staticmethod
  def _usernameIdOrId(m):
    return (f'{m.chat.username}|{m.chat.id}'
            if m.chat.username is not None
            else m.chat.id)
