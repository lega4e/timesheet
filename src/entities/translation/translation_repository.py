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
    
  def add(self, translation: Translation):
    translation.addListener(self._onTranslationEmitDestroy,
                            event=Translation.EMIT_DESTROY)
    translation.connect()
    lira_id = self.lira.put(translation.serialize(), cat='translation')
    self.lira.flush()
    self._translations[translation.id] = (lira_id, translation)
    
  def removeTranslations(self, predicat: Callable):
    print('REMOVE TRANSLATIONS')
    trs = [tr for _, tr in self._translations.values() if predicat(tr)]
    for tr in trs:
      tr.emitDestroy()

  def _onTranslationEmitDestroy(self, translation):
    print(f'ON TRANS EMIT DEST {translation.id}')
    if self._translations.get(translation.id) is None:
      return
    print('found')
    lira_id, translation = self._translations.get(translation.id)
    self.lira.pop(lira_id)
    self.lira.flush()
    self._translations.pop(translation.id)
    translation.dispose()
    
  def _deserializeTranslations(self) -> {int: (int, Translation)}:
    trs = {}
    for lira_id in self.lira['translation']:
      tr = self.lira.get(id=lira_id)
      print(tr)
      tr = self.translationFactory.make(serialized=tr)
      tr.addListener(self._onTranslationEmitDestroy,
                     event=Translation.EMIT_DESTROY)
      trs[tr.id] = (lira_id, tr)
    return trs