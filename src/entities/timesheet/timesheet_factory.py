from typing import Any

from src.entities.event.event_repository import EventRepository
from src.entities.timesheet.timesheet import Timesheet
from src.utils.lira import Lira


class TimesheetFactory:
  def __init__(
    self,
    lira: Lira,
    event_repository: EventRepository,
  ):
    self.lira = lira
    self.eventRepository = event_repository
    
  def make(
    self,
    id: int = None,
    name: str = None,
    serialized: {str : Any} = None
  ) -> Timesheet:
    return Timesheet(
      event_repository=self.eventRepository,
      id=id,
      name=name,
      serialized=serialized,
    )
