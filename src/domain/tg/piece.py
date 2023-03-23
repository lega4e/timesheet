from copy import deepcopy
from typing import List, Union

from telebot.types import MessageEntity

from src.entities.message_maker.emoji import get_emoji
from src.utils.utils import reduce_list


class _Piece:
  def __init__(
    self,
    text: str,
    url: str = None,
    type: str = None,
    types: List[str] = None,
    user = None
  ):
    self.text = text
    self.url = url
    self.user = user
    self.types = {val for val in
                  [*(types or []), type, None if url is None else 'text_link']
                  if val is not None}
    
class Pieces:
  def __init__(self, pieces: List[_Piece] = None, emoji: str = None):
    self.pieces = pieces or []
    self.emoji = emoji
    
  def toMessage(self):
    return self.toString(), self.getEntities()
    
  def toString(self):
    emoji = get_emoji(self.emoji)
    return ((f'{emoji} ' if emoji is not None else '')
            + ''.join([p.text for p in self.pieces]))
  
  def getEntities(self) -> List[MessageEntity]:
    emoji = get_emoji(self.emoji)
    if emoji is not None:
      self.pieces = [_Piece(f'{emoji} ')] + self.pieces
    types = reduce_list(lambda a, b: a | b, [p.types for p in self.pieces], set())
    entities = reduce_list(lambda a, b: a + b, [self.getEntitiesWithType(type) for type in types], [])
    if emoji is not None:
      self.pieces = list(self.pieces[1:])
    return entities
    
  def getEntitiesWithType(self, type: str) -> List[MessageEntity]:
    pos = 0
    entities = []
    for piece in self.pieces:
      text_length = _count_chars(piece.text)
      if type not in piece.types:
        pos += text_length
        continue
      if (len(entities) != 0 and
          entities[-1].offset + entities[-1].length == pos and
          (type != 'text_link' or entities[-1].url == piece.url)):
        entities[-1].offset += text_length
      else:
        entities.append(MessageEntity(
          type=type,
          offset=pos,
          length=text_length,
          url=piece.url,
        ))
      pos += text_length
    return entities

  def __add__(self, other):
    if isinstance(other, str):
      return self.__add__(Pieces([_Piece(other)]))
    if isinstance(other, _Piece):
      return self.__add__(Pieces([other]))
    me = deepcopy(self)
    me += other
    return me
  
  def __iadd__(self, other):
    if isinstance(other, str):
      return self.__iadd__(Pieces([_Piece(other)]))
    if isinstance(other, _Piece):
      return self.__iadd__(Pieces([other]))
    other = deepcopy(other)
    if (len(self.pieces) != 0 and len(other.pieces) != 0 and
        self.pieces[-1].types == other.pieces[0].types and
        self.pieces[-1].url == other.pieces[0].url and
        self.pieces[-1].user == other.pieces[0].user):
      self.pieces[-1].text += other.pieces[0].text
      self.pieces += other.pieces[1:]
    else:
      self.pieces += other.pieces
    self.emoji = other.emoji or self.emoji
    return self


def P(
  text: str = None,
  types: Union[List[str], str] = None,
  url: str = None,
  user = None,
  emoji: str = None
):
  if isinstance(types, str):
    types = [types]
  return Pieces([_Piece(text, url=url, types=types, user=user)]
                if text is not None else [],
                emoji=emoji)


def _count_chars(text: str) -> int:
  count = 0
  for c in text:
    count += 1 if len(bytes(c, encoding='utf-8')) < 4 else 2
  return count
