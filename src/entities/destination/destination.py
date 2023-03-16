from typing import Any

from src.entities.destination.settings import DestinationSettings
from src.utils.notifier import Notifier
from src.utils.serialize import Serializable


class Destination(Notifier, Serializable):
  """
  Все поля не nullable
  """
  def __init__(
    self,
    chat = None,
    sets: DestinationSettings = None,
    serialized: {str, Any} = None,
  ):
    Notifier.__init__(self)
    if serialized is not None:
      self.deserialize(serialized)
    else:
      assert(chat is not None)
      self.chat = chat
      self.sets = sets or DestinationSettings()
    self.sets.addListener(lambda _: self.notify())

  def serialize(self) -> {str: Any}:
    return {
      'chat': self.chat,
      'sets': self.sets.serialize()
    }

  def deserialize(self, serialized: {str: Any}):
    self.chat = serialized['chat']
    self.sets = DestinationSettings(serialized=serialized['sets'])
    
  def getUrl(self, message_id: int = None):
    chat = str(self.chat) if isinstance(self.chat, int) else self.chat[1:]
    return f't.me/{chat}' + ('' if message_id is None else f'/{message_id}')

