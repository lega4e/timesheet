from typing import Optional

from src.domain.locator import LocatorStorage, Locator
from src.entities.destination.destination import Destination
from src.entities.destination.settings import DestinationSettings
from src.utils.lira import Lira


class DestinationRepo(LocatorStorage):
  def __init__(self, locator: Locator):
    super().__init__(locator)
    self.lira: Lira = self.locator.lira()
    self.destinations: {int: (int, Destination)} = self._deserializeDestinations()

  def create(self, chat, sets: DestinationSettings):
    counter = self.lira.get('destination_counter', 0)
    counter += 1
    destination = Destination(id=counter, chat=chat, sets=sets)
    self.lira.put(counter, id='destination_counter', cat='id_counter')
    lira_id = self.lira.put(destination.serialize(), cat='destination')
    self.lira.flush()
    destination.addListener(self._onDestinationChanged)
    self.destinations[destination.id] = (lira_id, destination)
    return destination

  def find(self, id) -> Optional[Destination]:
    d = self.destinations.get(id)
    return None if d is None else d[1]
  
  def findByChat(self, chat) -> Destination:
    for _, destination in self.destinations.values():
      if destination.chat == chat:
        return destination
    return self.create(chat, sets=DestinationSettings())
  
  def _deserializeDestinations(self) -> {int, (int, Destination)}:
    destinations = {}
    for lira_id in self.lira['destination']:
      destination = Destination(serialized=self.lira.get(id=lira_id))
      destination.addListener(self._onDestinationChanged)
      destinations[destination.id] = (lira_id, destination)
    return destinations
  
  def _onDestinationChanged(self, destination: Destination):
    lira_id, destination = self.destinations[destination.id]
    self.lira.put(destination.serialize(), id=lira_id, cat='destination')
    self.lira.flush()