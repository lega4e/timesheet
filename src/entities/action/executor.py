from typing import cast

from src.domain.locator import LocatorStorage, Locator
from src.entities.action.action import Action, ActionTgAutoForward
from src.entities.destination.destination import Destination
from src.entities.timesheet.timesheet import Timesheet
from src.entities.translation.translation import Translation
from src.utils.repeater import PeriodRepeater


class ActionExecutor(LocatorStorage):
  def __init__(self, locator: Locator):
    super().__init__(locator)
    self.tg = self.locator.tg()
    self.timesheetRepo = self.locator.timesheetRepo()
    self.destinationRepo = self.locator.destinationRepo()
    self.translationRepo = self.locator.translationRepo()
    self.msgMaker = self.locator.messageMaker()
    
  def makeRepeater(self, action: Action) -> PeriodRepeater:
    return PeriodRepeater(
      action=lambda: self.__call__(action),
      period=action.period,
      on_last_update_changed=action.setLastUpdate,
      check_period=5,
    )
    
  def __call__(self, action: Action):
    if action.type == Action.TG_AUTO_FORWARD:
      self._tgAutoForward(cast(ActionTgAutoForward, action))
      
  def _tgAutoForward(self, action: ActionTgAutoForward):
    timesheet: Timesheet = self.timesheetRepo.find(action.timesheetId)
    destination: Destination = self.destinationRepo.findByChat(action.chat.chatId)
    if timesheet is None:
      return
    if action.translationId is not None:
      tr = self.translationRepo.find(action.translationId)
      if tr is not None:
        tr.emitDestroy('remove by autoforward')
      action.translationId = None
    tr = self.translationRepo.putWithId(lambda id: Translation(
      locator=self.locator,
      id=id,
      destination=destination,
      timesheet_id=timesheet.id,
      creator=action.creator,
    ))
    if tr is not None:
      action.translationId = tr.id
    action.notify()
