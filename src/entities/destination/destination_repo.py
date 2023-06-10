from typing import Callable, Any

from src.domain.locator import Locator
from src.utils.tg.tg_destination import TgDestination
from src.entities.destination.destination import Destination
from src.utils.lira_repo import LiraRepo


T = Destination
Key = int


class DestinationRepo(LiraRepo):
  def __init__(self, locator: Locator):
    super().__init__(locator.lira(), lira_cat='destination')

  def valueToSerialized(self, value: T) -> {str: Any}:
    return value.serialize()

  def valueFromSerialized(self, serialized: {str: Any}) -> T:
    return Destination(serialized=serialized)

  def addValueListener(self, value: T, listener: Callable):
    value.addListener(listener)

  def keyByValue(self, value: T) -> Key:
    return value.id
    
  def findByChatId(self, chatId) -> Destination:
    destination = self.findIf(lambda d: d.chat.chatId == chatId)
    if destination is not None:
      return destination
    return self.put(Destination(
      id=self.newId(),
      chat=TgDestination(chat_id=chatId)
    ))
