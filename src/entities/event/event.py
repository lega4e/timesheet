from datetime import datetime
from typing import Any

from src.utils.notifier import Notifier


class Place:
  PLOT = 'PLOT'
  TOCHKA = 'TOCHKA'
  BOILER_HOUSE = 'BOILER_HOUSE'
  
  def __init__(self, name: str):
    self.name = name


class Event(Notifier):
  def __init__(
    self,
    start: datetime = None,
    finish: datetime = None,
    place: Place = None,
    url: str = None,
    desc: str = None,
    creator: int = None,  # (user chat_id)
    id: id = None,
    serialized: {str: Any} = None,
  ):
    super().__init__()
    if serialized is None:
      self.start = start
      self.finish = finish
      self.place = place
      self.url = url
      self.desc = desc
      self.creator = creator
      self.id = id
    else:
      self.start = serialized['start']
      self.finish = serialized['finish']
      self.place = serialized['place']
      self.url = serialized['url']
      self.desc = serialized['desc']
      self.creator = serialized['creator']
      self.id = serialized['id']

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
