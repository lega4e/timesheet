from typing import Any

from src.entities.event.event_repository import EventRepository
from src.entities.message_maker.piece import Piece
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
    password: str = None,
    head: [Piece] = None,
    tail: [Piece] = None,
    serialized: {str : Any} = None
  ) -> Timesheet:
    return Timesheet(
      event_repository=self.eventRepository,
      id=id,
      name=name,
      password=password,
      head=head,
      tail=tail,
      serialized=serialized,
    )
