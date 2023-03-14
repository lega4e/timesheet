from datetime import datetime
from typing import Any

from src.utils.notifier import Notifier


class Place:
  PLOT = 'Плоt'
  TOCHKA = '• точка •'
  BOILER_HOUSE = 'Котельная'
  TLL = 'ТЛЛ'
  TODD = 'ТОДД'
  DJERRIK = 'Джеррик'
  
  def __init__(self, name: str):
    self.name = name
    
    
class EventField:
  START_TIME = 'START_TIME_FIELD'
  FINISH_TIME = 'FINISH_TIME_FIELD'
  PLACE = 'PLACE_FIELD'
  URL = 'URL_FIELD'
  DESC = 'DESC_FIELD'


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
      self.start = serialized.get('start')
      self.finish = serialized.get('finish')
      self.place = serialized.get('place')
      self.url = serialized.get('url')
      self.desc = serialized.get('desc')
      self.creator = serialized.get('creator')
      self.id = serialized.get('id')

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
