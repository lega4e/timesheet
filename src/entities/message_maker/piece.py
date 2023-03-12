from typing import Union, List

from telebot.types import MessageEntity

from src.entities.message_maker.emoji import emoji


class Piece:
  def __init__(self, text: str, url: str = None, type: str = None):
    self.text = text
    self.url = url
    self.type = type


def piece2string(pieces: [Piece]) -> str:
  return ''.join([p.text for p in pieces])


def piece2message(
  message: Union[List[Piece], str],
  edit=False,
  warning=False,
  ok=False,
  fail=False,
) -> (str, [MessageEntity]):
  entities = None
  if isinstance(message, list):
    e = emoji('', edit=edit, warning=warning, ok=ok, fail=fail)
    if e != '':
      message = [Piece(e)] + message
    message, entities = piece2string(message), piece2entities(message)
  else:
    message = emoji(message, edit=edit, warning=warning, ok=ok, fail=fail)
  return message, entities


def piece2entities(pieces: [Piece]) -> [MessageEntity]:
  pos = 0
  entities = []
  for piece in pieces:
    if piece.url is not None:
      entities.append(MessageEntity(
        type='text_link',
        offset=pos,
        length=count_chars(piece.text),
        url=piece.url,
      ))
    elif piece.type is not None:
      entities.append(MessageEntity(
        type=piece.type,
        offset=pos,
        length=count_chars(piece.text),
      ))
    pos += count_chars(piece.text)
  return entities


def count_chars(text: str) -> int:
  count = 0
  for c in text:
    count += 1 if len(bytes(c, encoding='utf-8')) < 4 else 2
  return count
