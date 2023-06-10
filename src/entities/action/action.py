import datetime as dt

from typing import Any

from src.utils.tg.tg_destination import TgDestination
from src.utils.notifier import Notifier
from src.utils.repeater import Period


class Action(Notifier):
  EMIT_DESTROY = 'ACTION_EMIT_DESTROY'
  TG_AUTO_FORWARD = 'ACTION_TG_AUTO_FORWARD'

  def __init__(
    self,
    id: int,
    creator: int,
    type: str,
    period: Period,
    last_update: dt.datetime = None,
  ):
    super().__init__()
    self.id = id
    self.creator = creator
    self.type = type
    self.period = period
    self.lastUpdate = last_update
      
  def setLastUpdate(self, last_update: dt.datetime):
    self.lastUpdate = last_update
    self.notify()


class ActionTgAutoForward(Action):
  def __init__(
    self,
    id: int,
    creator: int,
    period: Period,
    chat: TgDestination,
    timesheet_id: int,
    last_update: dt.datetime = None,
    translation_id: int = None,
  ):
    super().__init__(
      id=id,
      creator=creator,
      type=Action.TG_AUTO_FORWARD,
      period=period,
      last_update=last_update
    )
    self.chat = chat
    self.timesheetId = timesheet_id
    self.translationId = translation_id


def serialize_action(action: Action) -> {str: Any}:
  serialized = {
      'id': action.id,
      'creator': action.creator,
      'type': action.type,
      'period': action.period,
      'last_update': action.lastUpdate,
    }
  if action.type == Action.TG_AUTO_FORWARD:
    serialized['chat'] = action.__dict__['chat']
    serialized['timesheet_id'] = action.__dict__['timesheetId']
    serialized['translation_id'] = action.__dict__['translationId']
  return serialized


def deserialize_action(serialized: {str: Any}) -> Action:
  type = serialized['type']
  creator = serialized['creator']
  id = serialized['id']
  period = serialized['period']
  lastUpdate = serialized['last_update']
  if type == Action.TG_AUTO_FORWARD:
    return ActionTgAutoForward(
      id=id,
      creator=creator,
      period=period,
      last_update=lastUpdate,
      chat=serialized['chat'],
      timesheet_id=serialized['timesheet_id'],
      translation_id=serialized['translation_id'],
    )
  else:
    raise Exception(f'Unknown type of action: {type}')