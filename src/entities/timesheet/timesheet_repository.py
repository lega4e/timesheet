from typing import Optional

from src.entities.timesheet.timesheet import Timesheet
from src.entities.timesheet.timesheet_factory import TimesheetFactory
from src.utils.lira import Lira


class TimesheetRepository:
  def __init__(
    self,
    timesheet_factory: TimesheetFactory,
    lira: Lira,
  ):
    self.timesheetFactory = timesheet_factory
    self.lira = lira
    self.timesheets = self._deserializeTimesheets()
  
  def create(self, name: str, pswd: str) -> Timesheet:
    counter = self.lira.get('timesheet_counter', 0)
    counter += 1
    timesheet = self.timesheetFactory.make(name=name, password=pswd, id=counter)
    self.lira.put(counter, id='timesheet_counter', cat='id_counter')
    lira_id = self.lira.put(timesheet.serialize(), cat='timesheet')
    self.lira.flush()
    timesheet.addListener(self._onTimesheetChanged)
    self.timesheets[timesheet.id] = (lira_id, timesheet)
    return timesheet
  
  def find(self, id: int) -> Optional[Timesheet]:
    t = self.timesheets.get(id)
    return None if t is None else t[1]
  
  def _deserializeTimesheets(self) -> {int: (int, Timesheet)}:
    timesheets = {}
    for lira_id in self.lira['timesheet']:
      timesheet = self.timesheetFactory.make(serialized=self.lira.get(id=lira_id))
      timesheet.addListener(self._onTimesheetChanged)
      timesheets[timesheet.id] = (lira_id, timesheet)
    return timesheets
  
  def _onTimesheetChanged(self, timesheet: Timesheet):
    lira_id, timesheet = self.timesheets[timesheet.id]
    self.lira.put(timesheet.serialize(), id=lira_id, cat='timesheet')
    self.lira.flush()
