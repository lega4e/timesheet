from typing import Union, List

from telebot import TeleBot
from telebot.types import Message

from src.domain.locator import glob
from src.domain.tg.tg_chat import TgChat
from src.entities.message_maker.piece import Piece, piece2message


def send_message(
  tg: TeleBot,
  chat_id: Union[TgChat, str, int],
  text: Union[str, List[Piece]],
  entities = None,
  disable_web_page_preview = True,
  reply_markup = None,
  answer_callback_query_id: int = None,
  answer_callback_query_text: str = None,
  emoji: str = None,
) -> Message:
  
  if entities is None:
    text, entities = piece2message(text, emoji=emoji)
    
  kwargs = {
    'text': text,
    'entities' : entities,
    'disable_web_page_preview' : disable_web_page_preview,
    'reply_markup' : reply_markup,
  }
  
  if isinstance(chat_id, int) or isinstance(chat_id, str):
    kwargs['chat_id'] = chat_id
  else:
    kwargs['chat_id'] = chat_id.chatId

  if isinstance(chat_id, TgChat) and chat_id.messageId is not None:
    m = tg.edit_message_text(message_id=chat_id.messageId, **kwargs)
  else:
    if isinstance(chat_id, TgChat) and chat_id.type == TgChat.TOPIC:
      kwargs['reply_to_message_id'] = chat_id.topicId
    m = tg.send_message(**kwargs)
    
  if answer_callback_query_id is not None:
    tg.answer_callback_query(
      callback_query_id=answer_callback_query_id,
      text=answer_callback_query_text or text,
    )

  if not isinstance(chat_id, TgChat) or chat_id.messageId is None:
    glob().flogger().message(text,
                             chat_id=kwargs['chat_id'],
                             entities=entities,
                             emoji=emoji,
                             disable_web_page_preview=disable_web_page_preview)
  return m