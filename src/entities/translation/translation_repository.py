from typing import Callable, Any, Optional, List

from src.domain.locator import Locator, LocatorStorage
from src.entities.translation.translation import Translation
from src.utils.lira_repo import LiraRepo


T = Translation
Key = int



class TranslationRepo(LocatorStorage, LiraRepo):
  def __init__(self, locator: Locator):
    LocatorStorage.__init__(self, locator)
    LiraRepo.__init__(self, self.locator.lira(), lira_cat='translation')
    for tr in [tr for _, tr in self.values.values()]:
      tr.connect()

  def valueToSerialized(self, value: T) -> {str: Any}:
    return value.serialize()

  def valueFromSerialized(self, serialized: {str: Any}) -> T:
    return Translation(self.locator, serialized=serialized)

  def addValueListener(self, value: T, listener: Callable):
    value.addListener(listener)
    value.addListener(self._onTranslationEmitDestroy,
                      event=Translation.EMIT_DESTROY)

  def keyByValue(self, value: T) -> Key:
    return value.id

  def put(self, value: T):
    raise Exception('Unimplemented')
    
  def putWithId(self, builder: Callable) -> Optional[T]:
    value = builder(self.newId())
    if not value.connect():
      return None
    super().put(value)
    return value
    
  def remove(self, key: Key) -> Optional[T]:
    translation: Translation = self.find(key)
    if translation is None:
      return None
    translation.emitDestroy('remove function')
    return translation
  
  def removeAll(self, predicat: Callable) -> [T]:
    trs: List[Translation] = self.findAll(predicat)
    for tr in trs:
      tr.emitDestroy('removeAll function')
    
  def _onTranslationEmitDestroy(self, translation):
    super().remove(translation.id)
