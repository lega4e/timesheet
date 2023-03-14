from telebot import TeleBot

from src.entities.event.event import Place
from src.utils.tg.tg_input_field import TgInputField, InputFieldButton
from src.utils.tg.value_validators import *


class TgEventInputFieldsConstructor:
  def __init__(self, tg: TeleBot, chat):
    self.tg = tg
    self.chat = chat
    
  def make_name_input_field(self, on_field_entered: Callable) -> TgInputField:
    return TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите название мероприятия',
      on_field_entered=on_field_entered,
      validator=TextValidator(),
    )
  
  def make_datetime_input_field(self, on_field_entered: Callable) -> TgInputField:
    return TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите дату и время начала мероприятия',
      on_field_entered=on_field_entered,
      validator=ChainValidator([DatetimeValidator(), CorrectDatetimeValidator()]),
    )

  def make_place_input_field(self, on_field_entered: Callable) -> TgInputField:
    return TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Выберете или введите место или организатора мероприятия',
      on_field_entered=on_field_entered,
      validator=TextValidator(),
      buttons=[
        [InputFieldButton(
          title=place,
          data=place,
        ) for place in [Place.PLOT, Place.TOCHKA, Place.BOILER_HOUSE]],
        [InputFieldButton(
          title=place,
          data=place,
        ) for place in [Place.TLL, Place.TODD, Place.DJERRIK]],
      ]
    )
  
  def make_url_input_field(self, on_field_entered: Callable) -> TgInputField:
    return TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите ссылку на мероприятие',
      on_field_entered=on_field_entered,
      validator=UrlValidator(),
      buttons=[[InputFieldButton(title='Пропустить', data=None)]]
    )
