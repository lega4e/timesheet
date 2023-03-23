from datetime import datetime
from typing import Any, Union

from src.utils.notifier import Notifier
from src.utils.serialize import Serializable


class Place:
  def __init__(self, name: str, org: str = None):
    self.name = name
    self.org = org
    
    
class Event(Notifier, Serializable):
  def __init__(
    self,
    start: datetime = None,
    finish: datetime = None,
    place: Place = None,
    url: str = None,
    desc: str = None,
    creator: Union[int, str] = None, # (user chat_id)
    id: id = None,
    serialized: {str: Any} = None,
  ):
    Notifier.__init__(self)
    if serialized is not None:
      self.deserialize(serialized)
    else:
      self.start = start
      self.finish = finish
      self.place = place
      self.url = url
      self.desc = desc
      self.creator = creator
      self.id = id

  def serialize(self) -> {str: Any}:
    return {
      'start': self.start,
      'finish': self.finish,
      'place': self.place,
      'url': self.url,
      'desc': self.desc,
      'creator': self.creator,
      'id': self.id,
    }
  
  def deserialize(self, serialized: {str: Any}):
    self.start = serialized.get('start')
    self.finish = serialized.get('finish')
    self.place = serialized.get('place')
    if 'org' not in self.place.__dict__.keys():
      self.place.org = None
    self.url = serialized.get('url')
    self.desc = serialized.get('desc')
    self.creator = serialized.get('creator')
    if self.creator is None:
      self.creator = None
    self.id = serialized.get('id')
