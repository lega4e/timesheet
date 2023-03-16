from typing import Callable, Any

from src.domain.locator import Locator
from src.entities.destination.destination import Destination
from src.utils.lira_repo import LiraRepo


T = Destination
Key = int


class DestinationRepo(LiraRepo):
  def __init__(self, locator: Locator):
    super().__init__(locator, lira_cat='destination')

  def valueToSerialized(self, value: T) -> {str: Any}:
    return value.serialize()

  def valueFromSerialized(self, serialized: {str: Any}) -> T:
    return Destination(serialized=serialized)

  def addValueListener(self, value: T, listener: Callable):
    value.addListener(listener)

  def keyByValue(self, value: T) -> Key:
    return value.chat

  def find(self, chat, **kargs) -> Destination:
    return super().find(chat, lambda c: Destination(chat=c))
