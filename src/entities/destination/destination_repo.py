from typing import Callable, Any

from src.domain.locator import Locator
from src.domain.tg.tg_chat import TgChat
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
    return value.id
    
  def findByChat(self, chat) -> Destination:
    destination = self.findIf(lambda d: d.chat.chatId == chat)
    if destination is not None:
      return destination
    return self.putWithId(
      lambda id: Destination(id=id, chat=TgChat(type=TgChat.PUBLIC,chat_id=chat))
    )
