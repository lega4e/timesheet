from typing import Iterable, Any, Callable

from src.entities.event.event import Event
from src.entities.event.event_repository import EventRepository
from src.utils.notifier import Notifier


class Timesheet(Notifier):
  EVENT_CHANGED = 'EVENT_CHANGED'
  
  def __init__(
    self,
    event_repository: EventRepository,
    id: int = None,
    name: str = None,
    events: {(int, Callable)} = None,
    serialized: {str : Any} = None
  ):
    super().__init__()
    self.eventRepository = event_repository
    if serialized is None:
      self.id = id
      self.name = name
      self._events: {int: Callable} = events or dict()
    else:
      self.id = int(serialized['id'])
      self.name = str(serialized['name'])
      self._events = {
        id : self.eventRepository.find(id).addListener(self._onEventChanged)
        for id in serialized['events']
      }
      
  def serialize(self) -> {str : Any}:
    return {
      'id': self.id,
      'name': self.name,
      'events': {id for id, callback in self._events.items()},
    }

  def addEvent(self, id: int):
    self._events[id] = (self.eventRepository
                            .find(id)
                            .addListener(self._onEventChanged))
    self.notify()
  
  def removeEvent(self, id: int) -> bool:
    if self._events.get(id) is None:
      return False
    self._events.pop(id)
    self.notify()
    return True

  def events(self, predicat = lambda _: True) -> Iterable[Event]:
    events = [self.eventRepository.find(id) for id, _ in self._events.items()]
    events = [e for e in events if e is not None and predicat(e)]
    return events
  
  def _onEventChanged(self, _):
    self.notify(event=Timesheet.EVENT_CHANGED)
