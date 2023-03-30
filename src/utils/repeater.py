import datetime as dt
import math
import time

from threading import Thread
from typing import Callable


class Repeater(Thread):
  def __init__(self, action: Callable, period: float):
    super().__init__()
    self.runFlag = False
    self.action = action
    self.counter = 0
    self.period = period
    
  def start(self):
    self.runFlag = True
    super().start()
    
  def stop(self):
    self.runFlag = False
    self.counter = 0
  
  def run(self):
    while self.runFlag:
      self.action(self.counter)
      self.counter += 1
      time.sleep(self.period)


class Period:
  def __init__(
    self,
    point: dt.datetime = None,
    delta: dt.timedelta = None
  ):
    self.point = point
    self.delta = delta


class PeriodRepeater(Repeater):
  def __init__(
    self,
    action: Callable,
    period: Period = None,
    on_last_update_changed: Callable = None,
    check_period: float = 1,
  ):
    self.periodAction = action
    self.actionPeriod = period
    self.lastUpdate = dt.datetime.now()
    self.onLastUpdateChanged = on_last_update_changed
    self.checkPeriod = check_period
    if self.actionPeriod.point is None:
      self.actionPeriod.point = dt.datetime.now()
    super().__init__(self._periodRepeatorAction, self.checkPeriod)
    
  def _periodRepeatorAction(self, _):
    now = dt.datetime.now()
    if self.lastUpdate < self._findNextPoint() <= now:
      self.lastUpdate = now
      if self.onLastUpdateChanged is not None:
        self.onLastUpdateChanged(self.lastUpdate)
      self.periodAction()
  
  def _findNextPoint(self) -> dt.datetime:
    k = math.ceil((self.lastUpdate.timestamp() - self.actionPeriod.point.timestamp())
                  / self.actionPeriod.delta.total_seconds())
    return self.actionPeriod.point + self.actionPeriod.delta * k
