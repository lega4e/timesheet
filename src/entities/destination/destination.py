from copy import copy
from typing import Any

from src.domain.tg.tg_chat import TgChat
from src.utils.tg.tg_destination import TgDestination
from src.entities.destination.settings import DestinationSettings
from src.utils.notifier import Notifier
from src.utils.serialize import Serializable


class Destination(Notifier, Serializable):
  """
  Все поля не nullable
  """
  def __init__(
    self,
    id: int = None,
    chat: TgDestination = None,
    sets: DestinationSettings = None,
    serialized: {str, Any} = None,
  ):
    Notifier.__init__(self)
    if serialized is not None:
      self.deserialize(serialized)
    else:
      assert(chat is not None and id is not None)
      self.id = id
      self.chat = chat
      self.sets = sets or DestinationSettings()
    self.sets.addListener(lambda _: self.notify())

  def serialize(self) -> {str: Any}:
    return {
      'id': self.id,
      'chat': self.chat,
      'sets': self.sets.serialize()
    }

  def deserialize(self, serialized: {str: Any}):
    self.id = serialized['id']
    self.chat = serialized['chat']
    if isinstance(self.chat, int) or isinstance(self.chat, str):
      self.chat = TgDestination(chat_id=self.chat)
    elif isinstance(self.chat, TgChat):
      self.chat = TgDestination(chat_id=self.chat.chatId,
                                message_to_replay_id=self.chat.topicId,
                                translate_to_message_id=self.chat.messageId)
    self.sets = DestinationSettings(serialized=serialized['sets'])
    
  def getUrl(self, message_id: int = None):
    chat = copy(self.chat)
    chat.translateToMessageId = message_id
    return chat.getUrl()

