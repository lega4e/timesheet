import json


class Config:
  CONFIG_FILE_NAME = 'config.json'

  def __init__(self):
    self.data = dict()
    with open(Config.CONFIG_FILE_NAME) as file:
      self.data = json.load(file)

  def loggingDefaultChats(self) -> [int]:
    return self._paramOrNone('logging_default_chats', list)

  def loggingDateFormat(self) -> str:
    return self._paramOrNone('logging_date_format', str)

  def loggingFormat(self) -> str:
    return self._paramOrNone('logging_format', str)

  def token(self) -> str:
    return self._paramOrNone('token', str)

  def _paramOrNone(self, name: str, tp):
    return Config._valueOrNone(self.data.get(name), tp)

  @staticmethod
  def _valueOrNone(value, tp):
    return value if type(value) is tp else None
