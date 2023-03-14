from typing import Any, Callable

from src.domain.locator import Locator, LocatorStorage
from src.entities.translation.translation import Translation
from src.utils.lira import Lira


class TranslationFactory(LocatorStorage):
  def __init__(self, locator: Locator):
    super().__init__(locator)
    self.lira: Lira = self.locator.lira()
    
  def make(
    self,
    event_predicat: Callable = None,
    chat_id: int = None,
    message_id: int = None,
    timesheet_id: int = None,
    serialized: {str: Any} = None,
  ) -> Translation:
    counter = None
    if serialized is None:
      counter = self.lira.get('translation_counter', 0)
      counter += 1
      self.lira.put(counter, id='translation_counter', cat='id_counter')
      self.lira.flush()
    return Translation(
      locator=self.locator,
      id=counter,
      event_predicat=event_predicat,
      chat_id=chat_id,
      message_id=message_id,
      timesheet_id=timesheet_id,
      serialized=serialized,
    )