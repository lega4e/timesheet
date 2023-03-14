from typing import Union, List

from telebot import TeleBot
from telebot.types import Message

from src.domain.locator import glob
from src.entities.message_maker.piece import Piece, piece2message


def send_message(
  tg: TeleBot,
  chat_id,
  text: Union[str, List[Piece]],
  entities = None,
  disable_web_page_preview = True,
  reply_markup = None,
  answer_callback_query_id: int = None,
  answer_callback_query_text: str = None,
  emoji: str = None,
) -> Message:
  if entities is None:
    message, ent = piece2message(text, emoji=emoji)
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
    
  glob().flogger().message(text,
                           entities=entities,
                           emoji=emoji,
                           disable_web_page_preview=disable_web_page_preview)
  return m