from typing import Callable

from src.entities.translation.translation import Translation
from src.entities.translation.translation_factory import TranslationFactory
from src.utils.lira import Lira


class TranslationRepo:
  def __init__(
    self,
    translation_factory: TranslationFactory,
    lira: Lira,
  ):
    self.translationFactory = translation_factory
    self.lira = lira
    self._translations = self._deserializeTranslations()
    for _, tr in self._translations.values():
      tr.connect()
    
  def add(self, translation: Translation) -> bool:
    translation.addListener(self._onTranslationEmitDestroy,
                            event=Translation.EMIT_DESTROY)
    if not translation.connect():
      return False
    lira_id = self.lira.put(translation.serialize(), cat='translation')
    self.lira.flush()
    self._translations[translation.id] = (lira_id, translation)
    return True
    
  def removeTranslations(self, predicat: Callable):
    trs = [tr for _, tr in self._translations.values() if predicat(tr)]
    for tr in trs:
      tr.emitDestroy()

  def _onTranslationEmitDestroy(self, translation):
    if self._translations.get(translation.id) is None:
      return
    lira_id, translation = self._translations.get(translation.id)
    self.lira.pop(lira_id)
    self.lira.flush()
    self._translations.pop(translation.id)
    translation.dispose()
    
  def _deserializeTranslations(self) -> {int: (int, Translation)}:
    trs = {}
    for lira_id in self.lira['translation']:
      tr = self.lira.get(id=lira_id)
      tr = self.translationFactory.make(serialized=tr)
      tr.addListener(self._onTranslationEmitDestroy,
                     event=Translation.EMIT_DESTROY)
      trs[tr.id] = (lira_id, tr)
    return trs