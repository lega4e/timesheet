from abc import abstractmethod
from typing import Optional, TypeVar, Callable, List, Any

from src.utils.lira import Lira

T = TypeVar('T')
Key = TypeVar('Key')


class LiraRepo:
  """
  Базовый класс для классов, представляющих собой репозиторий сериализуемых объектов, сохраняющихся на диске с
  помощью Lira
  """
  LIRA_COUNTER_ID_CATEGORY = 'id_counter'
  
  
  def __init__(self, lira: Lira, lira_cat: str, lira_counter_id: str = None):
    """
    :param lira: объект Lira, с помощью которого будут сохраняться объекты
    
    :param lira_cat: категория объектов, которая будет использоваться в Lira
    
    :param lira_counter_id: идентификатор счётчика идентификаторов (будет сформирован автоматически)
    """
    self.lira = lira
    self.liraCat = lira_cat
    self.liraCounterId = (lira_cat + '_id_counter'
                          if lira_counter_id is None else
                          lira_counter_id)
    self.values: {Key, (int, T)} = self._deserializeValues()


  @abstractmethod
  def valueToSerialized(self, value: T) -> {str: Any}:
    """
    Преобразование объекта в формат, который можно сериалозовать (с помощью picle)
    
    :param value: значение, которые нужно сераилозовать
    
    :return: сериализованное значение
    """
    pass


  @abstractmethod
  def valueFromSerialized(self, serialized: {str: Any}) -> T:
    """
    Получение значения из сериализованного объекта
    
    :param serialized: сериализованный объект
    
    :return: десериализованный объект
    """
    pass


  @abstractmethod
  def addValueListener(self, value: T, listener: Callable):
    """
    Эта функция должна добавлять слушание изменения объекта (т.е. функция listener должна вызываться
    каждый раз, как изменяется объект value). Требуется, чтобы на диске было всегда актуальное состояние объекта
    
    :param value: значение, которое нужно слушать
    
    :param listener: колбэк, который нужно вызывать, когда значение изменяется
    """
    pass


  @abstractmethod
  def keyByValue(self, value: T) -> Key:
    """
    Получение ключа, по которому хранить значение в репозитории из самого значения
    
    :param value: значение
    :return: ключ
    """
    pass


  def put(self, value: T) -> T:
    """
    Добавить значение в репозиторий
    
    :param value: значение, которое нужно добавить
    
    :return: возвращает value
    """
    lira_id = self.lira.put(self.valueToSerialized(value), cat=self.liraCat)
    self.lira.flush()
    self.values[self.keyByValue(value)] = lira_id, value
    self.addValueListener(value, self._onValueChanged)
    return value
  

  def find(self, key: Key, maker: Callable = None, with_id: bool = False) -> Optional[T]:
    """
    Найти значение по ключу; если значение не найдено и указано поле maker, то объект создаётся вызовом этой
    функции, где в качестве первого аргумента передаётся ключ; если при этом ещё и указано поле with_id,
    то вторым аругемонт в maker передаётся новое id для значения
    
    :param key: ключ, по которому нужно найти значение
    
    :param maker: функция создания значения (первым аргументом должна принимать ключ)
    
    :param with_id: нужно ли в функцию создания значения передавать вторым аргументом новое id
    
    :return: найденный или созданный объект или None
    """
    value = self.values.get(key)
    if value is not None:
      return value[1]
    if maker is None:
      return None
    value = maker(key, self.newId()) if with_id else maker(key)
    self.put(value)
    return value
  
  
  def findIf(self, predicat: Callable) -> Optional[T]:
    """
    Найти первый объект, который удовлетворяет предикату
    
    :param predicat: условие, по которому следует выбрать значение
    
    :return: найденное значение или None
    """
    for _, value in self.values.values():
      if predicat(value):
        return value
    return None
  
  
  def findAll(self, predicat: Callable) -> List[T]:
    """
    Найти все объекты, которые удовлетворяют предикату
    
    :param predicat: условие, которому объекты должны удовлетворять
    
    :return: найденные объекты
    """
    return [value for _, value in self.values.values() if predicat(value)]


  def remove(self, key: Key) -> Optional[T]:
    """
    Удалить значение из репозитория по ключу и вернуть его; если значение не найдено, выбрасывается исключение
    
    :param key: ключ, по которому нужно удалить значение
    
    :return: удаление значение
    """
    try:
      lira_id, value = self.values.pop(key)
      self.lira.pop(id=lira_id)
      self.lira.flush()
      return value
    except KeyError:
      return None


  def removeAll(self, predicat: Callable) -> [T]:
    """
    Удалить все значения, которые удовлетворяют предикату
    
    :param predicat: условие, которум должны удовлетворять объекты для удаления
    
    :return: список всех удалённых объектов
    """
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
    """
    Вернуть новое уникальное значение (идентификатор) для нового объекта
    
    :return: идентификатор
    """
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


# END