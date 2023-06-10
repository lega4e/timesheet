import random

from typing import Callable, Optional, List, Union

from telebot import TeleBot
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .send_message import send_message
from .piece import P, Pieces
from .tg_state import TgState
from .value_validators import Validator, ValidatorObject


class InputFieldButton:
  """
  Одна из кнопок, которую можно нажать вместо ручного ввода значения
  """
  def __init__(self, title: str, data, answer: str = None):
    """
    :param title: какой текст будет отображён на кнопке
    :param data: какое значение будет возвращено как "введённое"
    :param answer: что будет отображено в инфо-шторке при нажатии на кнопку
    """
    self.title = title
    self.data = data
    self.answer = answer
    self.qb = str(random.random())


class TgInputField(TgState):
  """
  Представляет собой класс для запроса единичного значения у пользователя. Позволяет:
  - Выводить приглашение к вводу
  - Выводить сообщение, если ввод прерван
  - Проверять корректность ввода данных с помощью класса Validator (и выводить сообщение об ошибке, в случае ошибки)
  - Устанавливать кнопки, по нажатию на которые возвращается любые данные в качестве введённых
  - Вызывает коллбэк, когда значение успешно введено (или нажата кнопка)
  """
  def __init__(
    self,
    tg: TeleBot,
    chat,
    greeting: Union[str, Pieces],
    validator: Validator,
    on_field_entered: Callable,
    terminate_message: Union[str, Pieces] = None,
    buttons: List[List[InputFieldButton]] = None,
  ):
    """
    :param tg: телебот, используется для отправки сообщений
    
    :param chat: чат, куда посылать приглашения к вводу или сообщение о прерванном вводе
    
    :param greeting: приглашение к вводу
    
    :param validator: класс валидатора поля — проверяет, корректно ли введено значение
    
    :param on_field_entered: коллбэк, вызывающийся, когда поле введено
    
    :param terminate_message: сообщение, отображающееся, когда ввод прерван
    
    :param buttons: кнопки, с помощью которых человек может выбирать значение
    """
    self.tg = tg
    self.chat = chat
    self.validator = validator
    self.onFieldEntered = on_field_entered
    self.terminateMessage = terminate_message
    if isinstance(self.terminateMessage, str):
      self.terminateMessage = P(self.terminateMessage)
    if self.terminateMessage is not None:
      self.terminateMessage.emoji = 'warning'
    self.buttons = buttons
    if isinstance(greeting, str):
      greeting = P(greeting)
    greeting.emoji = 'edit'
    super().__init__(lambda: send_message(tg=self.tg,
                                          chat=self.chat,
                                          text=greeting,
                                          reply_markup=self._makeMarkup()))


  # OVERRIDE METHODS
  def _onTerminate(self):
    """
    Когда ввод прерван, выводим сообщение о прерванном вводе
    """
    if self.terminateMessage is not None:
      send_message(tg=self.tg,
                   chat=self.chat,
                   text=self.terminateMessage)
      
      
  def _handleMessage(self, m: Message):
    """
    Обрабатываем сообщение: проверяем, что оно корректно (с помощью валидатора), выводим ошибку, если ошибка,
    и вызываем коллбэк, если корректно
    
    :param m: сообщение, которое нужно обработать
    """
    answer = self.validator.validate(ValidatorObject(message=m))
    if not answer.success:
      send_message(tg=self.tg,
                   chat=self.chat,
                   text=answer.error)
    else:
      self.onFieldEntered(answer.data)
    return True


  def _handleCallbackQuery(self, q: CallbackQuery):
    """
    Обрабатываем нажатие на кнопки
    
    :param q: запрос (нажатие на кнопку), которое нужно обработать
    :return: получилось ли обработать запрос (тогда и только тогда, когда нужная кнопка нажата)
    """
    if self.buttons is None:
      return False
    for row in self.buttons:
      for button in row:
        if q.data == button.qb:
          self.tg.answer_callback_query(callback_query_id=q.id,
                                        text=button.answer or f'Выбрано {button.title}')
          self.onFieldEntered(button.data)
          return True
    return False


  # SERVICE METHODS
  def _makeMarkup(self) -> Optional[InlineKeyboardMarkup]:
    """
    Создаём разметку для кнопок
    
    :return: Разметка для кнопок (если кнопки указаны)
    """
    if self.buttons is None:
      return None
    markup = InlineKeyboardMarkup()
    for row in self.buttons:
      markup.add(*[InlineKeyboardButton(text=b.title, callback_data=b.qb)
                   for b in row],
                 row_width=len(row))
    return markup

  def _handleMessageBefore(self, m: Message) -> bool:
    """
    Никак не обрабатываем сообщение перед подсостоянием
    :return: всегда False
    """
    pass
