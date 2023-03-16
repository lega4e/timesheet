from typing import Callable, Any

from src.domain.locator import Locator
from src.entities.timesheet.timesheet import Timesheet
from src.utils.lira_repo import LiraRepo


T = Timesheet
Key = int


class TimesheetRepo(LiraRepo):
  def __init__(self, locator: Locator):
    super().__init__(locator, lira_cat='timesheet')

  def valueToSerialized(self, value: T) -> {str: Any}:
    return value.serialize()

  def valueFromSerialized(self, serialized: {str: Any}) -> T:
    return Timesheet(locator=self.locator, serialized=serialized)

  def addValueListener(self, value: T, listener: Callable):
    value.addListener(listener)

  def keyByValue(self, value: T) -> Key:
    return value.id

  def findByName(self, name: str):
    return self.findIf(lambda t: t.name == name)
