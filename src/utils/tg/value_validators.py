import re

from abc import abstractmethod
from copy import copy
from typing import Callable, Union, List

from chakert import Typograph
from telebot.types import Message

from src.entities.event.event_fields_parser import parse_datetime, correct_datetime
from src.entities.message_maker.piece import Piece



class ValidatorObject:
  def __init__(
    self,
    success: bool = True,
    data = None,
    error: Union[str, List[Piece]] = None,
    emoji: str = None,
    message: Message = None,
  ):
    self.success = success
    self.data = data
    self.error = error
    self.emoji = emoji
    self.message = message



class Validator:
  def validate(self, o: ValidatorObject) -> ValidatorObject:
    return self._validate(copy(o))

  @abstractmethod
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    pass



class TextValidator(Validator):
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    o.data = Typograph('ru').typograph_text(o.message.text, 'ru')
    return o


class FunctionValidator(Validator):
  def __init__(self, function: Callable):
    self.function = function
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    return self.function(o)
  
  
  
class ChainValidator(Validator):
  def __init__(self, validators: [Validator]):
    self.validators = validators
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    for validator in self.validators:
      o = validator.validate(o)
      if not o.success:
        break
    return o
  
  

class OrValidator(Validator):
  def __init__(self, validators: [Validator]):
    self.validators = validators
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    for validator in self.validators:
      obj = validator.validate(o)
      if obj.success:
        return obj
    return obj
  
  
  
class IntValidator(Validator):
  def __init__(self, error: str = None):
    self.error = error or 'Нужно ввести просто число'

  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    if re.match(r'^\d+$', o.message.text) is None:
      o.success, o.error, o.emoji = False, self.error, 'warning'
    else:
      o.data = int(o.message.text)
    return o
 


class PieceValidator(Validator):
  def __init__(self, let_none = True):
    self.letNone = let_none
    
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    o.data = (None if self.letNone and o.message.text.lower() in ['none', 'нет']
              else [Piece(o.message.text)])
    return o



class IdValidator(Validator):
  PSWD_ERROR_MESSAGE = ('Ошибочка. Пароль может состоять '
                        'только из латинских букв, цифр и символов '
                        'нижнего подчёркивания')
  
  NAME_ERROR_MESSAGE = ('Ошибочка. Название может состоять '
                        'только из латинских букв, цифр и символов '
                        'нижнего подчёркивания и не может '
                        'начинаться цифрой')
  
  def __init__(self, error: Union[str, List[Piece]], is_password=False):
    self.error = error
    self.isPassword = is_password
 
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    regexpr = r'^\w+$' if self.isPassword else r'^[a-zA-Z_]\w+$'
    if re.match(regexpr, o.message.text) is None:
      o.success, o.error, o.emoji = False, self.error, 'warning'
      return o
    else:
      o.data = o.message.text
    return o
 
 
 
class TgPublicGroupOrChannelValidator(Validator):
  def __init__(self, error: str = None):
    self.error = error or [
      Piece('Ссылка на канал или группу должна иметь вид '),
      Piece('@channel_or_group_login', type='code'),
      Piece(' или '),
      Piece('https://t.me/channel_or_group_login', type='code')
    ]
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    m = re.match(r'^(https?://)?t\.me/(\w+)$', o.message.text)
    if m is not None:
      o.data = '@' + m.group(2)
      return o
    m = re.match(r'^@?(\w+)$', o.message.text)
    if m is not None:
      o.data = '@' + m.group(1)
      return o
    o.success, o.error, o.emoji = False, self.error, 'warning'
    return o



class TgMessageUrlValidator(Validator):
  def __init__(self, error: str = None):
    self.error = error or [
      Piece('Ссылка на сообщение должна иметь вид '),
      Piece('https://t.me/channel_or_group_login/5', type='code')
    ]
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    m = re.match(r'^(https?://)?t\.me/(\w+)/(\d+)$', o.message.text)
    if m is not None:
      o.data = ('@' + m.group(2), int(m.group(3)))
    else:
      o.success, o.error, o.emoji = False, self.error, 'warning'
    return o



class DatetimeValidator(Validator):
  def __init__(self, error: str = None):
    self.error = error
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    datetime, error = parse_datetime(o.message.text)
    if datetime is None:
      o.success, o.error, o.emoji = False, self.error or error, 'warning'
    else:
      o.data = datetime
    return o



class CorrectDatetimeValidator(Validator):
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    o.data = correct_datetime(o.data)
    return o



class UrlValidator(Validator):
  def __init__(self, error: str = None):
    self.error = error or 'Что-то не похоже на ссылку :( давай ещё разок'
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    if re.match(r'^https?://.+\..+$', o.message.text) is None:
      o.success, o.error, o.emoji = False, self.error, 'fail'
    else:
      o.data = o.message.text
    return o
