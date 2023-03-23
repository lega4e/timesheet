from copy import copy
from typing import List, Callable

from telebot import TeleBot
from telebot.types import CallbackQuery, Message

from src.domain.tg.api import send_message
from src.utils.tg.tg_input_field import TgInputField
from src.utils.tg.tg_state import TgState
from src.utils.utils import CallbackWrapper


class TgInputForm(TgState):
  def __init__(
    self,
    tg: TeleBot,
    chat,
    on_form_entered: Callable,
    fields: List[TgInputField],
    terminate_message: str = None,
  ):
    super().__init__(on_enter_state=self._onEnterState)
    assert(len(fields) != 0)
    self.tg = tg
    self.chat = chat
    self.fields = fields
    self.onFormEntered = on_form_entered
    self.terminate_message = terminate_message
    self.data = [None] * len(self.fields)
    callbacks = [copy(field.onFieldEntered) for field in self.fields]
    for i in range(len(self.fields)):
      def on_field_entered(data, num):
        callbacks[num](data)
        self._onFieldDataEntered(data)
      self.fields[i].onFieldEntered = CallbackWrapper(on_field_entered, num=copy(i))

  
  # OVERRIDE METHODS
  def _onTerminate(self):
    if self.terminate_message is not None:
      send_message(tg=self.tg,
                   chat_id=self.chat,
                   text=self.terminate_message)

  def _handleMessage(self, m: Message) -> bool:
    raise Exception('Сообщение всегда должно обрабатываться в TgInputField')

  def _handleCallbackQuery(self, q: CallbackQuery) -> bool:
    return False
  
  # MAIN METHODS
  def _onEnterState(self):
    self.setTgState(self.fields[0])
    
  def _onFieldDataEntered(self, data):
    index = self.fields.index(self._substate)
    self.data[index] = data
    if index + 1 < len(self.fields):
      self.setTgState(self.fields[index+1])
    else:
      self.onFormEntered(self.data)

  def _handleMessageBefore(self, m: Message) -> bool:
    pass
