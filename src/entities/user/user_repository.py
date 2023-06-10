from typing import Callable, Any

from src.domain.locator import Locator, LocatorStorage
from src.entities.user.user import User
from src.utils.lira_repo import LiraRepo

T = User
Key = int

class UserRepo(LocatorStorage, LiraRepo):
  def __init__(self, locator: Locator):
    LocatorStorage.__init__(self, locator)
    LiraRepo.__init__(self, self.locator.lira(), lira_cat='user')
    
  def valueToSerialized(self, value: T) -> {str: Any}:
    return value.serialize()

  def valueFromSerialized(self, serialized: {str: Any}) -> T:
    return User(self.locator, serialized=serialized)

  def addValueListener(self, value: T, listener: Callable):
    value.addListener(listener)

  def keyByValue(self, value: T) -> Key:
    return value.chat

  def find(self, key: Key, **kwargs) -> T:
    return super().find(key, lambda chat: User(self.locator, chat=chat))
