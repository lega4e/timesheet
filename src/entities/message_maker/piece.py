from telebot.types import MessageEntity


class Piece:
  def __init__(self, text: str, url: str = None, type: str = None):
    self.text = text
    self.url = url
    self.type = type


def piece2string(pieces: [Piece]) -> str:
  return ''.join([p.text for p in pieces])


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
