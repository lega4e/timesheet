from typing import Callable, Any, Optional

from src.domain.locator import Locator
from src.entities.action.action import Action, serialize_action, deserialize_action
from src.utils.lira_repo import LiraRepo


T = Action
Key = int


class ActionRepo(LiraRepo):
  def __init__(self, locator: Locator):
    super().__init__(locator.lira(), lira_cat='action')
    self.executor = locator.actionExecutor()
    self.actionIsStarted = False
    self.repeaters = []
  
  def valueToSerialized(self, value: T) -> {str: Any}:
    return serialize_action(value)

  def valueFromSerialized(self, serialized: {str: Any}) -> T:
    return deserialize_action(serialized)

  def addValueListener(self, value: T, listener: Callable):
    value.addListener(listener)
    value.addListener(self._onActionEmitDestroy,
                      event=Action.EMIT_DESTROY)

  def keyByValue(self, value: T) -> Key:
    return value.id

  def put(self, value: T):
    super().put(value)
    repeater = self.executor.makeRepeater(value)
    repeater.actionId = value.id
    self.repeaters.append(repeater)
    repeater.start()

  def remove(self, key: Key) -> Optional[T]:
    action = self.find(key)
    if action is not None:
      action.notify(Action.EMIT_DESTROY)
    return action
      

  def startActions(self):
    if self.actionIsStarted:
      return
    for action in self.findAll(lambda _: True):
      repeater = self.executor.makeRepeater(action)
      repeater.actionId = action.id
      self.repeaters.append(repeater)
    for repeater in self.repeaters:
      repeater.start()
    self.actionIsStarted = True
    
  def stopActions(self):
    if not self.actionIsStarted:
      return
    for repeater in self.repeaters:
      repeater.stop()
    self.actionIsStarted = False
    
  def _onActionEmitDestroy(self, action):
    for repeater in self.repeaters:
      if repeater.actionId == action.id:
        repeater.stop()
    super().remove(action.id)