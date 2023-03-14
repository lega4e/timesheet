from typing import Optional

from src.domain.locator import Locator, LocatorStorage
from src.entities.event.event import Event
from src.entities.event.event_factory import EventFactory
from src.utils.lira import Lira


class EventRepository(LocatorStorage):
  def __init__(
    self,
    locator: Locator,
  ):
    super().__init__(locator)
    self.lira: Lira = self.locator.lira()
    self.eventFactory: EventFactory = self.locator.eventFactory()
    self._events = self._deserializeEvents()
    
  def add(self, event: Event):
    lira_id = self.lira.put(event.serialize(), cat='event')
    self.lira.flush()
    dispose = event.addListener(self._onEventChanged)
    self._events[event.id] = (lira_id, dispose, event)
    
  def remove(self, id: int) -> bool:
    if self._events.get(id) is None:
      return False
    lira_id, dispose, _ = self._events.pop(id)
    dispose()
    self.lira.pop(lira_id)
    self.lira.flush()
    return True
  
  def find(self, id: int) -> Optional[Event]:
    event = self._events.get(id)
    return None if event is None else event[2]

  def _deserializeEvents(self) -> {int : (int, Event)}:
    events = {}
    for lira_id in self.lira['event']:
      event = self.eventFactory.make(serialized=self.lira.get(id=lira_id))
      dispose = event.addListener(self._onEventChanged)
      events[event.id] = (lira_id, dispose, event)
    return events
  
  def _onEventChanged(self, event: Event):
    lira_id, _, event = self._events.get(event.id)
    self.lira.put(event.serialize(), id=lira_id, cat='event')
    self.lira.flush()