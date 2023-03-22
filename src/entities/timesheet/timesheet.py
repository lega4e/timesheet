from typing import Any, Callable

from src.domain.locator import LocatorStorage, Locator
from src.entities.destination.settings import DestinationSettings
from src.entities.event.event import Event
from src.entities.event.event_repository import EventRepo
from src.utils.notifier import Notifier
from src.utils.serialize import Serializable


class Timesheet(Notifier, LocatorStorage, Serializable):
  EMIT_PLACES_CHANGED = 'EMIT_PLACES_CHANGED'
  
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
    self.eventRepo: EventRepo = self.locator.eventRepo()
    if serialized is not None:
      self.deserialize(serialized)
    else:
      self.id = id
      self.name = name
      self.password = password
      self.destinationSets = destination_sets or DestinationSettings()
      self.destinationSets.addListener(lambda s: self.notify())
      self._events: {int: Callable} = dict()
      self.places = []
    
  def serialize(self) -> {str : Any}:
    return {
      'id': self.id,
      'name': self.name,
      'password': self.password,
      'destination_sets': self.destinationSets.serialize(),
      'events': {id for id, callback in self._events.items()},
      'places': self.places,
    }
  
  def deserialize(self, serialized: {str: Any}):
    self.id: int = serialized['id']
    self.name: str = serialized['name']
    self.password: str = serialized.get('password')
    self.destinationSets = DestinationSettings(serialized=serialized.get('destination_sets'))
    if serialized.get('head') is not None:
      self.destinationSets.head = serialized.get('head')
    if serialized.get('tail') is not None:
      self.destinationSets.tail = serialized.get('tail')
    self.destinationSets.addListener(lambda s: self.notify())
    events = [self.eventRepo.find(id) for id in serialized['events']]
    self._events = {
      event.id: event.addListener(lambda e: self.notify())
      for event in events
      if event is not None
    }
    self.places = serialized.get('places') or []

  def addEvent(self, id: int):
    self._events[id] = (self.eventRepo
                            .find(id)
                            .addListener(lambda e: self.notify()))
    self.notify()
  
  def removeEvent(self, id: int) -> bool:
    if self._events.get(id) is None:
      return False
    self._events.pop(id)
    self.eventRepo.remove(id)
    self.notify()
    return True

  def events(self, predicat = lambda _: True) -> [Event]:
    events = [self.eventRepo.find(id) for id, _ in self._events.items()]
    events = [e for e in events if e is not None and predicat(e)]
    return events
