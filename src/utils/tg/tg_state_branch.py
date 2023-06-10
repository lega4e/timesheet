import random
from copy import copy
from typing import Callable, Optional

from telebot import TeleBot
from telebot.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from .send_message import send_message
from .tg_destination import TgDestination
from .tg_state import TgState


class BranchButton:
  """
  Кнопка, по нажатию на которую устанавливается подсостояние
  """
  def __init__(
    self,
    title: str,
    state: TgState = None,
    action: Callable = None,
    callback_answer: str = None
  ):
    """
    :param title: строка, которая будет отображатся на кнопке
    
    :param state: состояние, которое будет остановлено после нажатия на кнопку
    
    :param action: действие, которое будет вызвано, по нажатию на кнопку
    
    :param callback_answer: сообщение, которое нарисуется пользователю в инфо-шторке
    """
    self.title = title
    self.state = state
    self.action = action
    self.callbackAnswer = callback_answer
    self.qb = str(random.random())


class TgStateBranch(TgState):
  """
  Сообщение в телеграмме, под которым есть кнопки; нажав на любую из кнопок будет установлено соответствующее
  подсостояние; как только это состояние завершится, будет снова установлено корневое состояние. Если будет
  нажата другая кнопка до того, как предыдущее подсостояние не завершится, оно будет прервано и установлено новое.
  Вместо установки новых состояний можно назначать коллбэки
  """
  def __init__(
    self,
    tg: TeleBot,
    chat: TgDestination,
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
    """Вызовите, если нужно обновить корневое сообщение"""
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
    chat = copy(self.chat)
    chat.translateToMessageId = self.messageId
    kwargs = {
      'chat': chat,
      'text': self.makeMessage(),
      'reply_markup': self._makeMarkup(),
    }
    self.messageId = send_message(tg=self.tg, **kwargs).message_id
