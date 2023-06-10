from typing import Union

from telebot import TeleBot
from telebot.types import Message

from src.domain.locator import glob
from .tg_destination import TgDestination, proveTgDestination
from .piece import Pieces, provePiece


def send_message(
  tg: TeleBot,
  chat: Union[TgDestination, str, int],
  text: Union[str, Pieces],
  disable_web_page_preview = True,
  reply_markup = None,
  answer_callback_query_id: int = None,
  answer_callback_query_text: str = None,
) -> Message:
  """
  Отправляет или обновляет сообщение в телеграм
  
  :param tg: Телебот
  
  :param chat: куда отправить (или какое сообщение обновить)
  
  :param text: текст, который отправить
  
  :param disable_web_page_preview: см. Telebot.send_message()
  
  :param reply_markup: см. Telebot.send_message()
  
  :param answer_callback_query_id: см. Telebot.send_message()
  
  :param answer_callback_query_text: см. Telebot.send_message()
  
  :return: то же, что и Telebot.send_message()
  """
  chat = proveTgDestination(chat)
  pieces = provePiece(text)
  text, entities = pieces.toMessage()
  if len(text) > 3900:
    m = None
    for i in range(0, len(text), 3900):
      m = send_message(tg,
                       chat,
                       pieces[i:i+3900],
                       disable_web_page_preview=disable_web_page_preview,
                       reply_markup=reply_markup,
                       answer_callback_query_id=answer_callback_query_id,
                       answer_callback_query_text=answer_callback_query_text)
      answer_callback_query_id = None
      answer_callback_query_text = None
    return m

  kwargs = {
    'chat_id' : chat.chatId,
    'text' : text,
    'entities' : entities,
    'disable_web_page_preview' : disable_web_page_preview,
    'reply_markup' : reply_markup,
  }
  
  if chat.translateToMessageId is not None:
    m = tg.edit_message_text(message_id=chat.translateToMessageId, **kwargs)
  else:
    m = tg.send_message(**kwargs, reply_to_message_id=chat.messageToReplayId)
    
  if answer_callback_query_id is not None:
    tg.answer_callback_query(
      callback_query_id=answer_callback_query_id,
      text=answer_callback_query_text or text,
    )

  if chat.translateToMessageId is None:
    glob().flogger().message(text=pieces,
                             chat_id=kwargs['chat_id'],
                             disable_web_page_preview=disable_web_page_preview)
  return m