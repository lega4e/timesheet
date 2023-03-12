from typing import Union, List

from telebot import TeleBot
from telebot.types import Message

from src.entities.message_maker.piece import Piece, piece2message


def send_message(
  tg: TeleBot,
  chat_id: int,
  text: Union[str, List[Piece]],
  entities = None,
  disable_web_page_preview = True,
  reply_markup = None,
  answer_callback_query_id: int = None,
  answer_callback_query_text: str = None,
  edit = False,
  warning = False,
  ok = False,
  fail = False,
) -> Message:
  if entities is None:
    message, ent = piece2message(text,
                                      edit=edit,
                                      warning=warning,
                                      ok=ok,
                                      fail=fail)
  else:
    message, ent = text, entities
  m = tg.send_message(chat_id=chat_id,
                      text=message,
                      disable_web_page_preview=disable_web_page_preview,
                      reply_markup=reply_markup,
                      entities=ent)
  if answer_callback_query_id is not None:
    tg.answer_callback_query(
      callback_query_id=answer_callback_query_id,
      text=answer_callback_query_text or message,
    )
  from src.domain.di import glob
  logger = glob().flogger()
  logger.message(text,
                 entities=entities,
                 edit=edit,
                 warning=warning,
                 ok=ok,
                 fail=fail,
                 disable_web_page_preview=disable_web_page_preview)
  return m