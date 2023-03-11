from typing import Union, List

from telebot import TeleBot
from telebot.types import Message

from src.entities.message_maker.emoji import emoji
from src.entities.message_maker.piece import Piece, piece2entities, piece2string


def send_message(
  tg: TeleBot,
  chat_id: int,
  message: Union[str, List[Piece]],
  disable_web_page_preview = True,
  reply_markup = None,
  answer_callback_query_id: int = None,
  answer_callback_query_text: str = None,
  edit = False,
  warning = False,
  ok = False,
  fail = False,
) -> Message:
  entities = None
  if isinstance(message, list):
    e = emoji('', edit=edit, warning=warning, ok=ok, fail=fail)
    if e != '':
      message = [Piece(e)] + message
    message, entities = piece2string(message), piece2entities(message)
  else:
    message = emoji(message, edit=edit, warning=warning, ok=ok, fail=fail)
  m = tg.send_message(
    chat_id=chat_id,
    text=message,
    disable_web_page_preview=disable_web_page_preview,
    reply_markup=reply_markup,
    entities=entities,
  )
  if answer_callback_query_id is not None:
    tg.answer_callback_query(
      callback_query_id=answer_callback_query_id,
      text=answer_callback_query_text or message,
    )
  return m