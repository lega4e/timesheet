from datetime import datetime
from typing import Any

from src.domain.locator import LocatorStorage, Locator
from src.entities.event.event import Event, Place
from src.utils.lira import Lira


class EventFactory(LocatorStorage):
  def __init__(self, locator: Locator):
    super().__init__(locator)
    self.lira: Lira = self.locator.lira()
    
  def make(
    self,
    start: datetime = None,
    finish: datetime = None,
    place: Place = None,
    url: str = None,
    desc: str = None,
    creator: int = None, # (user chat_id)
    serialized: {str: Any} = None,
  ) -> Event:
    id = None
    if serialized is None:
      id = self.lira.get('event_counter', 0)
      id += 1
      self.lira.put(id, id='event_counter', cat='id_counter')
      self.lira.flush()
    return Event(
      start=start,
      finish=finish,
      place=place,
      url=url,
      desc=desc,
      creator=creator,
      id=id,
      serialized=serialized,
    )
