from typing import Any

from src.domain.locator import LocatorStorage, Locator
from src.entities.timesheet.timesheet import Timesheet


class TimesheetFactory(LocatorStorage):
  def __init__(self, locator: Locator):
    super().__init__(locator)
    
  def make(
    self,
    id: int = None,
    name: str = None,
    password: str = None,
    serialized: {str : Any} = None
  ) -> Timesheet:
    return Timesheet(
      locator=self.locator,
      id=id,
      name=name,
      password=password,
      serialized=serialized,
    )
