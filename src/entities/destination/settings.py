from typing import Any, List, Set

from src.domain.tg.piece import Pieces
from src.utils.notifier import Notifier
from src.utils.serialize import Serializable


class DestinationSettings(Notifier, Serializable):
  def __init__(
    self,
    head: Pieces = None,
    tail: Pieces = None,
    black_list: Set[int] = None,
    words_black_list: List[str] = None,
    line_format: str = None,
    serialized: {str: Any} = None,
  ):
    Notifier.__init__(self)
    if serialized is not None:
      self.deserialize(serialized)
    else:
      self.head = head
      self.tail = tail
      self.blackList = black_list or set()
      self.wordsBlackList = words_black_list or []
      self.lineFormat = line_format
  
  def serialize(self) -> {str: Any}:
    return {
      'head': self.head,
      'tail': self.tail,
      'black_list': self.blackList,
      'words_black_list': self.wordsBlackList,
      'line_format': self.lineFormat,
    }

  def deserialize(self, serialized: {str: Any}):
    self.head = serialized.get('head')
    if isinstance(self.head, list):
      self.head = None
    self.tail = serialized.get('tail')
    if isinstance(self.tail, list):
      self.tail = None
    self.blackList = set(serialized.get('black_list') or {})
    self.wordsBlackList = list(serialized.get('words_black_list') or [])
    self.lineFormat = serialized.get('line_format')

  @staticmethod
  def default():
    return DestinationSettings(
      line_format='👉 %s %p %n',
    )
  
  @staticmethod
  def merge(base, override):
    return DestinationSettings(
      head=override.head or base.head,
      tail=override.tail or base.tail,
      black_list=override.blackList | base.blackList,
      words_black_list=override.wordsBlackList + base.wordsBlackList,
      line_format=override.lineFormat or base.lineFormat,
    )