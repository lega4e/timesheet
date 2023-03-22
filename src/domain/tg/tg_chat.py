from typing import Union


class TgChat:
  CHAT = 'CHAT'
  PUBLIC = 'PUBLIC' # publich group or chat
  GROUP = 'GROUP' # group with < 0 id (not supergroup with topics)
  TOPIC = 'TOPIC'
  
  def __init__(
    self,
    type: str,
    chat_id: Union[int, str],
    topic_id: int = None,
    message_id: int = None,
  ):
    self.type = type
    self.chatId = chat_id
    self.topicId = topic_id
    self.messageId = message_id
    
  def getUrl(self):
    chat = str(self.chatId) if isinstance(self.chatId, int) else self.chatId[1:]
    return (f't.me/{chat}' +
            ('' if self.topicId is None else f'/{self.topicId}') +
            ('' if self.messageId is None else f'/{self.messageId}'))
