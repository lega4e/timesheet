from abc import abstractmethod
from typing import Callable

from telebot.types import CallbackQuery, Message


class TgState:
  def __init__(
    self,
    on_enter_state: Callable = None,
  ):
    self._onEnterState = on_enter_state
    self._substate = None
    
  def start(self):
    if self._onEnterState is not None:
      self._onEnterState()
      
  def terminate(self):
    self._onTerminate()
    
  def terminateSubstate(self):
    if self._substate is not None:
      self._substate.terminate()
      self.resetTgState()
    
  def setTgState(self, state, silent=False, terminate=True):
    if terminate:
      self.terminateSubstate()
    self._substate = state
    if not silent:
      state.start()
    
  def resetTgState(self):
    self._substate = None
  
  def handleMessage(self, m: Message) -> bool:
    if (self._handleMessageBefore(m) or
        (self._substate is not None and self._substate.handleMessage(m))):
      return True
    return self._handleMessage(m)

  def handleCallbackQuery(self, q: CallbackQuery) -> bool:
    if self._substate is not None and self._substate.handleCallbackQuery(q):
      return True
    return self._handleCallbackQuery(q)
  
  @abstractmethod
  def _onTerminate(self):
    pass
  
  @abstractmethod
  def _handleMessageBefore(self, m: Message) -> bool:
    pass

  @abstractmethod
  def _handleMessage(self, m: Message) -> bool:
    pass

  @abstractmethod
  def _handleCallbackQuery(self, q: CallbackQuery) -> bool:
    pass