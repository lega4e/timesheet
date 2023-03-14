from typing import Optional

from src.domain.locator import LocatorStorage, Locator
from src.entities.timesheet.timesheet import Timesheet
from src.entities.timesheet.timesheet_factory import TimesheetFactory
from src.utils.lira import Lira


class TimesheetRepo(LocatorStorage):
  def __init__(self, locator: Locator):
    super().__init__(locator)
    self.timesheetFactory: TimesheetFactory = self.locator.timesheetFactory()
    self.lira: Lira = self.locator.lira()
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
  
  def findByName(self, name) -> Optional[Timesheet]:
    for _, timesheet in self.timesheets.values():
      if timesheet.name == name:
        return timesheet
    return None
  
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
