from logging import Logger
from typing import List, Union

from telebot import TeleBot

from src.entities.message_maker.piece import Piece, piece2message


class FLogger:
  def __init__(
    self,
    logger: Logger,
    tg: TeleBot = None,
    chats: [int] = None,
  ):
    self.logger = logger
    self.tg = tg
    self.chats = chats or []

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
    entities = None,
    edit = False,
    warning = False,
    ok = False,
    fail = False,
    **kwargs
  ):
    print('message logger')
    if self.tg is None:
      return
    for chat in self.chats:
      if entities is None:
        message, ent = piece2message(pieces,
                                     edit=edit,
                                     warning=warning,
                                     ok=ok,
                                     fail=fail)
      else:
        message, ent = pieces, entities
      if message is not None:
        self.tg.send_message(chat_id=chat, text=message, entities=ent, **kwargs)

  @staticmethod
  def _usernameIdOrId(m):
    return (f'{m.chat.username}|{m.chat.id}'
            if m.chat.username is not None
            else m.chat.id)
