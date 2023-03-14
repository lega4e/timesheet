from typing import Any

from src.entities.destination.settings import DestinationSettings
from src.utils.notifier import Notifier
from src.utils.serialize import Serializable


class Destination(Notifier, Serializable):
  def __init__(
    self,
    id: int = None,
    chat = None,
    sets: DestinationSettings = None,
    serialized: {str, Any} = None,
  ):
    Notifier.__init__(self)
    if serialized is not None:
      self.deserialize(serialized)
    else:
      self.id = id
      self.chat = chat
      self.sets = sets or DestinationSettings()
    self.sets.addListener(self.notify)

  def serialize(self) -> {str: Any}:
    return {
      'id': self.id,
      'chat': self.chat,
      'sets': self.sets.serialize()
    }

  def deserialize(self, serialized: {str: Any}):
    self.id = serialized.get('id')
    self.chat = serialized.get('chat')
    self.sets = DestinationSettings(serialized=serialized.get('sets'))

