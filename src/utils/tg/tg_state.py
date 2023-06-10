from abc import abstractmethod
from typing import Callable

from telebot.types import CallbackQuery, Message


class TgState:
  """
  Представляет собой состояние, в котором находится телеграм бот. Позволяет:
  - установить события на вход и выход из состояния;
  - установить обработчики сообщений и запросов (перегрузите соответствующие функции)
  - устанавливать подсостояния, которым будет делегировать обработка сообщений и запросов
  """
  def __init__(
    self,
    on_enter_state: Callable = None,
  ):
    """
    :param on_enter_state: коллбэк, который вызывается при вхождении в состояние
    """
    self._onEnterState = on_enter_state
    self._substate = None
    
    
  def start(self) -> None:
    """
    Должно быть вызвано при вхождении в состояние
    """
    if self._onEnterState is not None:
      self._onEnterState()
      
      
  def terminate(self):
    """
    Должно быть вызвано после выхода из состояния
    """
    self._onTerminate()
    
  def terminateSubstate(self):
    """
    Вызывается, когда завершается подстотояние
    """
    if self._substate is not None:
      self._substate.terminate()
      self.resetTgState()
    
  def setTgState(self, state, silent=False, terminate=True):
    """
    Установка подсостояния
    
    :param state: подстотояние
    :param silent: вызывать ли метод start у состояния (по умолчанию вызывает)
    :param terminate: завершить ли предыдущее подсостояние (по умолчанию завершает)
    """
    if terminate:
      self.terminateSubstate()
    self._substate = state
    if not silent:
      state.start()
    
  def resetTgState(self):
    """
    Очищает подсостояние
    """
    self._substate = None
  
  def handleMessage(self, m: Message) -> bool:
    """
    Обрабатывает сообщение (можно перегрузить метод _handleMessageBefore в дочернем классе,
    чтобы перехватить обработку; если этот метод возвратет True, то на этом обработка сообщения
    завершится). Если есть подсостояние, то в первую очередь происходит попытка обработать
    сообщение с помощью подсостояния.
    
    :param m: сообщение, которое нужно обработать
    :return: было ли обработано состояние
    """
    if (self._handleMessageBefore(m) or
        (self._substate is not None and self._substate.handleMessage(m))):
      return True
    return self._handleMessage(m)

  def handleCallbackQuery(self, q: CallbackQuery) -> bool:
    """
    Обрабатывает CallbackQuery (если есть подсостояние, то сначала пытаемся обработать подсостоянием)
    
    :param q: запрос, который нужно обработать
    :return: был ли обработан запрос
    """
    if self._substate is not None and self._substate.handleCallbackQuery(q):
      return True
    return self._handleCallbackQuery(q)
  
  @abstractmethod
  def _onTerminate(self):
    """
    Вызывается при завершении состояния
    """
    pass
  
  @abstractmethod
  def _handleMessageBefore(self, m: Message) -> bool:
    """
    Обработка сообщения перед обработкой подсостоянием
    
    :param m: сообщение, которое нужно обработать
    :return: было ли обработано сообщение (следует ли остановить обработку?)
    """
    pass

  @abstractmethod
  def _handleMessage(self, m: Message) -> bool:
    """
    Обработка сообщения (уже после подсостояния)
    
    :param m: сообщение, которое нужно обработать
    :return: было ли обработано сообщение
    """
    pass

  @abstractmethod
  def _handleCallbackQuery(self, q: CallbackQuery) -> bool:
    """
    Обработа запроса callbackQuery
    
    :param q: запрос, который нужно обработать
    :return: был ли обработан запрос
    """
    pass