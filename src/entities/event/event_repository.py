from typing import Callable, Any

from src.domain.locator import Locator
from src.entities.event.event import Event
from src.utils.lira_repo import LiraRepo


T = Event
Key = int


class EventRepo(LiraRepo):
  def __init__(self, locator: Locator):
    super().__init__(locator, lira_cat='event')

  def valueToSerialized(self, value: T) -> {str: Any}:
    return value.serialize()

  def valueFromSerialized(self, serialized: {str: Any}) -> T:
    return Event(serialized=serialized)

  def addValueListener(self, value: T, listener: Callable):
    value.addListener(listener)

  def keyByValue(self, value: T) -> Key:
    return value.id