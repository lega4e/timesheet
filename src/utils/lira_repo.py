from abc import abstractmethod
from typing import Optional, TypeVar, Callable, List, Any

from src.domain.locator import Locator, LocatorStorage
from src.utils.lira import Lira

T = TypeVar('T')
Key = TypeVar('Key')


class LiraRepo(LocatorStorage):
  LIRA_COUNTER_ID_CATEGORY = 'id_counter'
  
  def __init__(self, locator: Locator, lira_cat: str, lira_counter_id: str = None):
    super().__init__(locator)
    self.lira: Lira = self.locator.lira()
    self.liraCat = lira_cat
    self.liraCounterId = (lira_cat + '_id_counter'
                          if lira_counter_id is None else
                          lira_counter_id)
    self.values: {Key, (int, T)} = self._deserializeValues()

  @abstractmethod
  def valueToSerialized(self, value: T) -> {str: Any}:
    pass

  @abstractmethod
  def valueFromSerialized(self, serialized: {str: Any}) -> T:
    pass

  @abstractmethod
  def addValueListener(self, value: T, listener: Callable):
    pass

  @abstractmethod
  def keyByValue(self, value: T) -> Key:
    pass

  def put(self, value: T):
    lira_id = self.lira.put(self.valueToSerialized(value), cat=self.liraCat)
    self.lira.flush()
    self.values[self.keyByValue(value)] = lira_id, value
    self.addValueListener(value, self._onValueChanged)
    
  def putWithId(self, builder: Callable) -> T:
    value = builder(self.newId())
    self.put(value)
    return value

  def find(self, key: Key, maker: Callable = None, with_id: bool = False) -> Optional[T]:
    value = self.values.get(key)
    if value is not None:
      return value[1]
    if maker is None:
      return None
    value = maker(key, self.newId()) if with_id else maker(key)
    self.put(value)
    return value
  
  def findIf(self, predicat: Callable) -> Optional[T]:
    for _, value in self.values.values():
      if predicat(value):
        return value
    return None
  
  def findAll(self, predicat: Callable) -> List[T]:
    return [value for _, value in self.values.values() if predicat(value)]

  def remove(self, key: Key) -> Optional[T]:
    try:
      lira_id, value = self.values.pop(key)
      self.lira.pop(id=lira_id)
      self.lira.flush()
      return value
    except KeyError:
      return None

  def removeAll(self, predicat: Callable) -> [T]:
    keys = []
    values = []
    for key, (lira_id, value) in self.values.items():
      if predicat(value):
        keys.append((key, lira_id))
        values.append(value)
    for key, lira_id in keys:
      self.values.pop(key)
      self.lira.pop(id=lira_id)
    self.lira.flush()
    return values

  def newId(self) -> int:
    counter = self.lira.get(id=self.liraCounterId, default=0)
    counter += 1
    self.lira.put(counter, id=self.liraCounterId, cat=LiraRepo.LIRA_COUNTER_ID_CATEGORY)
    self.lira.flush()
    return counter

  def _deserializeValues(self) -> {Key: (int, T)}:
    values = {}
    for lira_id in self.lira[self.liraCat]:
      value = self.valueFromSerialized(serialized=self.lira.get(id=lira_id))
      self.addValueListener(value, self._onValueChanged)
      values[self.keyByValue(value)] = lira_id, value
    return values
  
  def _onValueChanged(self, value: T):
    lira_id, value = self.values.get(self.keyByValue(value))
    self.lira.put(self.valueToSerialized(value), id=lira_id, cat=self.liraCat)
    self.lira.flush()
