import random
from typing import Callable, Optional

from telebot import TeleBot
from telebot.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from src.domain.tg.api import send_message
from src.entities.message_maker.piece import piece2message
from src.utils.tg.tg_state import TgState


class BranchButton:
  def __init__(
    self,
    title: str,
    state: TgState = None,
    action: Callable = None,
    callback_answer: str = None
  ):
    self.title = title
    self.state = state
    self.action = action
    self.callbackAnswer = callback_answer
    self.qb = str(random.random())


class TgStateBranch(TgState):
  def __init__(
    self,
    tg: TeleBot,
    chat,
    make_buttons: Callable,
    make_message: Callable,
    on_terminate: Callable = None,
  ):
    super().__init__(self._translateMessage)
    self.tg = tg
    self.chat = chat
    self.makeButtons = make_buttons
    self.makeMessage = make_message
    self.onTerminate = on_terminate
    self.messageId = None
    self.buttons = None
  
  
  # OVERRIDE METHODS
  def _onTerminate(self):
    if self.onTerminate is not None:
      self.onTerminate()

  def _handleMessageBefore(self, m: Message) -> bool:
    return False

  def _handleMessage(self, m: Message) -> bool:
    return False

  def _handleCallbackQuery(self, q: CallbackQuery) -> bool:
    if self.buttons is None:
      return False
    for row in self.buttons:
      for button in row:
        if q.data == button.qb:
          self.tg.answer_callback_query(
            callback_query_id=q.id,
            text=button.callbackAnswer or f'Выбрано {button.title}'
          )
          if button.action is not None:
            button.action()
          if button.state is not None:
            self.setTgState(button.state)
          return True
    return False


  # MAIN
  def updateMessage(self):
    self._translateMessage()


  # SERVICE METHODS
  def _makeMarkup(self) -> Optional[InlineKeyboardMarkup]:
    if self.buttons is None:
      return None
    markup = InlineKeyboardMarkup()
    for row in self.buttons:
      markup.add(*[InlineKeyboardButton(text=b.title, callback_data=b.qb)
                   for b in row],
                 row_width=len(row))
    return markup
  
  def _translateMessage(self):
    self.buttons = self.makeButtons()
    text, entities = piece2message(self.makeMessage())
    kwargs = {
      'chat_id': self.chat,
      'text': text,
      'reply_markup': self._makeMarkup(),
      'entities': entities,
    }
    if self.messageId is None:
      self.messageId = send_message(tg=self.tg, **kwargs).message_id
    else:
      kwargs['message_id'] = self.messageId
      self.tg.edit_message_text(**kwargs)
