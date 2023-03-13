from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.entities.event.event import Place


def place_markup() -> InlineKeyboardMarkup:
  markup = InlineKeyboardMarkup()
  markup.add(*[InlineKeyboardButton(name, callback_data=data)
               for data, name in
               place_to_str_map().items()],
             row_width=3)
  return markup


def place_to_str_map() -> {str: str}:
  return {
    Place.PLOT: 'Плоt',
    Place.TOCHKA: '• точка •',
    Place.BOILER_HOUSE: 'Котельная',
    Place.TLL: 'ТЛЛ',
    Place.TODD: 'ТОДД',
    Place.DJERRIK: 'Джеррик',
  }