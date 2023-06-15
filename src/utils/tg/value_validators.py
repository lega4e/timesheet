import re

from abc import abstractmethod
from copy import copy
from typing import Callable, Union, List

from chakert import Typograph
from telebot.types import Message

from src.entities.event.event_fields_parser import parse_datetime, correct_datetime
from src.utils.tg.piece import Pieces, P



class ValidatorObject:
  def __init__(
    self,
    success: bool = True,
    data = None,
    error: Union[str, Pieces] = None,
    message: Message = None,
  ):
    self.success = success
    self.data = data
    self.error = error
    self.message = message



class Validator:
  """
  Класс, который 1) проверяет значение на корректность, 2) меняет его, если надо
  """
  def validate(self, o: ValidatorObject) -> ValidatorObject:
    """
    Основная функция, возвращает результат валидации
    """
    return self._validate(copy(o))

  @abstractmethod
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    """
    Сама проверка, должна быть переопределена в конкретных классах
    """
    pass



class FalseValidator(Validator):
  """
  Всегда ошибка
  """
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    o.success = False
    return o



class TextValidator(Validator):
  """
  Ничего не проверяет, только улучшает текст с помощью типографа
  """
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    o.data = Typograph('ru').typograph_text(o.message.text, 'ru')
    return o


class FunctionValidator(Validator):
  """
  Позволяет задать валидатор не классом, а функцией
  """
  def __init__(self, function: Callable):
    self.function = function
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    return self.function(o)
  
  
  
class ChainValidator(Validator):
  """
  Логическое "и" при валидации (последовательно вызывает несколько валидаторов)
  """
  def __init__(self, validators: [Validator]):
    self.validators = validators
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    for validator in self.validators:
      o = validator.validate(o)
      if not o.success:
        break
    return o
  
  

class OrValidator(Validator):
  """
  Логическое "или" при валидации (выбираем первый попавшийся валидатор)
  """
  def __init__(self, validators: [Validator]):
    self.validators = validators
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    obj = o
    for validator in self.validators:
      obj = validator.validate(o)
      if obj.success:
        return obj
    return obj
  
  
  
class IntValidator(Validator):
  """
  Проверяет, что введённое значение число, преобразует к типу int
  """
  def __init__(self, error: str = None):
    self.error = error or P('Нужно ввести просто число', emoji='warning')

  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    if re.match(r'^-?\d+$', o.message.text) is None:
      o.success, o.error = False, self.error
    else:
      o.data = int(o.message.text)
    return o
 


class PieceValidator(Validator):
  """
  Ничего не проверяет, преобразует обрабатываемое сообщение в Pieces
  """
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    o.data = Pieces.fromMessage(o.message.text, o.message.entities)
    return o



class IdValidator(Validator):
  PSWD_ERROR_MESSAGE = ('Ошибочка. Пароль может состоять '
                        'только из латинских букв, цифр и символов '
                        'нижнего подчёркивания')
  
  NAME_ERROR_MESSAGE = ('Ошибочка. Название может состоять '
                        'только из латинских букв, цифр и символов '
                        'нижнего подчёркивания и не может '
                        'начинаться цифрой')
  
  def __init__(self, error: Union[str, Pieces], is_password=False):
    self.error = error
    self.isPassword = is_password
 
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    regexpr = r'^\w+$' if self.isPassword else r'^[a-zA-Z_]\w+$'
    if re.match(regexpr, o.message.text) is None:
      o.success, o.error = False, self.error
      return o
    else:
      o.data = o.message.text
    return o
 
 
 
class TgPublicGroupOrChannelValidator(Validator):
  def __init__(self, error: str = None):
    self.error = error or (
      P('Ссылка на канал или группу должна иметь вид ', emoji='warning') +
      P('@channel_or_group_login', types='code') +
      P(' или ') +
      P('https://t.me/channel_or_group_login', types='code')
    )
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    m = re.match(r'^(https?://)?t\.me/(\w+)/?$', o.message.text)
    if m is not None:
      o.data = '@' + m.group(2)
      return o
    m = re.match(r'^@?(\w+)$', o.message.text)
    if m is not None:
      o.data = '@' + m.group(1)
      return o
    o.success, o.error = False, self.error
    return o



class TgMessageUrlValidator(Validator):
  def __init__(self, error: str = None):
    self.error = error or (
      P('Ссылка на сообщение должна иметь вид ', emoji='warning') +
      P('https://t.me/channel_or_group_login/5', types='code')
    )
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    m = re.match(r'^(https?://)?t\.me/(\w+)/(\d+)$', o.message.text)
    if m is not None:
      o.data = ('@' + m.group(2), int(m.group(3)))
    else:
      o.success, o.error = False, self.error
    return o



class DatetimeValidator(Validator):
  def __init__(self, error: str = None):
    self.error = error
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    datetime, error = parse_datetime(o.message.text)
    if datetime is None:
      o.success, o.error = False, self.error or error
    else:
      o.data = datetime
    return o



class CorrectDatetimeValidator(Validator):
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    o.data = correct_datetime(o.data)
    return o



class TgUrlValidator(Validator):
  def __init__(self, error: str = None):
    self.error = error or 'Что-то не похоже на ссылку :( давай ещё разок'
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    m = re.match(r'^((https?://[^/]+.[^/])|(t\.me)|@(\w+))(/.+)?$', o.message.text)
    if m is None:
      o.success, o.error, o.emoji = False, self.error, 'fail'
    else:
      if m.group(4) is not None:
        o.data = 't.me/' + m.group(4)
      else:
        o.data = o.message.text
    return o


class IntegerListValidator(Validator):
  def __init__(self, error: str = None):
    self.error = error or (
      P('Что-то не так :( ожидается список чисел '
            '— просто числа, отделённые друг от друга '
            'пробелом и ничем больше. Например:\n',
        emoji='fail') +
      P('4 5 28 2', types='code')
    )
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    words: List[str] = o.data.split()
    try:
      values = [int(word) for word in words]
      o.data = values
    except:
      o.success, o.error = False, self.error
    return o



class WordListValidator(Validator):
  def __init__(self, error: str = None):
    self.error = error or (
      P('Что-то не так :( ожидается список слов; '
        'слова могут содержать только буквы, цифры и '
        'символы нижнего подчёркивания; слова отделяётся '
        'друг от друга пробелом и ничем больше. Например:\n',
        emoji='fail'),
      P('я_не_хочу_это_постить куй 666 ругательство', types='code'),
    )
  
  def _validate(self, o: ValidatorObject) -> ValidatorObject:
    words: List[str] = o.data.split()
    o.data = words
    for word in words:
      if re.match('\w+', word) is None:
        o.success, o.error = False, self.error
        return o
    return o
