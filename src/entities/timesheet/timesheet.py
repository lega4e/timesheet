from typing import Iterable, Any, Callable

from src.domain.locator import LocatorStorage, Locator
from src.entities.destination.settings import DestinationSettings
from src.entities.event.event import Event
from src.entities.event.event_repository import EventRepository
from src.entities.message_maker.piece import Piece
from src.utils.notifier import Notifier
from src.utils.serialize import Serializable


class Timesheet(Notifier, LocatorStorage, Serializable):
  EVENT_CHANGED = 'EVENT_CHANGED'
  
  def __init__(
    self,
    locator: Locator,
    id: int = None,
    name: str = None,
    password: str = None,
    destination_sets: DestinationSettings = None,
    serialized: {str : Any} = None
  ):
    Notifier.__init__(self)
    LocatorStorage.__init__(self, locator)
    self.eventRepository: EventRepository = self.locator.eventRepository()
    if serialized is not None:
      self.deserialize(serialized)
    else:
      self.id = id
      self.name = name
      self.password = password
      self.destinationSets = destination_sets or DestinationSettings()
      self.destinationSets.addListener(self.notify)
      self._events: {int: Callable} = dict()
    
  def serialize(self) -> {str : Any}:
    return {
      'id': self.id,
      'name': self.name,
      'password': self.password,
      'destination_sets': self.destinationSets.serialize(),
      'events': {id for id, callback in self._events.items()},
    }
  
  def deserialize(self, serialized: {str: Any}):
    self.id: int = serialized['id']
    self.name: str = serialized['name']
    self.password: str = serialized.get('password')
    self.destinationSets = DestinationSettings(serialized=serialized.get('destination_sets'))
    self.destinationSets.addListener(self.notify)
    if serialized.get('head') is not None:
      self.destinationSets.head = serialized.get('head')
    if serialized.get('tail') is not None:
      self.destinationSets.tail = serialized.get('tail')
    events = [self.eventRepository.find(id) for id in serialized['events']]
    self._events = {
      event.id: event.addListener(self._onEventChanged)
      for event in events
      if event is not None
    }

  def setHead(self, head: [Piece] = None):
    self.destinationSets.head = head
    self.destinationSets.notify()

  def setTail(self, tail: [Piece] = None):
    self.destinationSets.tail = tail
    self.destinationSets.notify()

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
