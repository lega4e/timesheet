from typing import Callable

from telebot import TeleBot
from telebot.types import CallbackQuery, MessageEntity, InlineKeyboardMarkup, InlineKeyboardButton

from src.entities.event.event import Event, EventField, Place
from src.entities.event.event_fields_parser import *


class EventTgEditor:
  EXIT = 'EXIT'
  
  def __init__(
    self,
    tg: TeleBot,
    on_finish: Callable,
    on_edit_field: Callable,
    event: Event,
    chat_id: int,
  ):
    self.tg = tg
    self.onFinish = on_finish
    self.onEdit = on_edit_field
    self.event = event
    self.chatId = chat_id
    self.state = None
    self.messageId = None

  def clear(self):
    self.state = None
    self.messageId = None
    
  def onStart(self):
    self.clear()
    self._translate()
    
  def handleText(self, text: str) -> bool:
    handler = {
      EventField.START_TIME: self._handleEnterStartTime,
      EventField.FINISH_TIME: self._handleEnterFinishTime,
      EventField.PLACE: self._handleEnterPlace,
      EventField.URL: self._handleEnterUrl,
      EventField.DESC: self._handleEnterDesc,
    }.get(self.state)
    if handler is None:
      return False
    else:
      handler(text)
      return True
    
  def callbackQuery(self, call: CallbackQuery):
    if call.data == self._cd(EventField.DESC):
      self.state = EventField.DESC
      self._send('Введите название мероприятия', call.id)
    elif call.data == self._cd(EventField.START_TIME):
      self.state = EventField.START_TIME
      self._send('Введите дату и время начала мероприятия', call.id)
    elif call.data == self._cd(EventField.FINISH_TIME):
      self.state = EventField.FINISH_TIME
      self._send('Введите продолжительность мероприятия (в минутах)', call.id)
    elif call.data == self._cd(EventField.PLACE):
      self.state = EventField.PLACE
      self._send('Введите место проведения мероприятия', call.id)
    elif call.data == self._cd(EventField.URL):
      self.state = EventField.URL
      self._send('Введите URL', call.id)
    elif call.data == self._cd(EventTgEditor.EXIT):
      self._send('Редактирование заверщено', call.id)
      self._finish()
    else:
      print(f'Неизвесный сигнал: {call.data}')
      
      
  # HANDLERS ENTER EVENT FIELD
  def _handleEnterStartTime(self, text: str):
    start, error = parse_datetime(text)
    if start is not None:
      start = correct_datetime(start, isfuture=True, delta=dt.timedelta(weeks=3))
      delta = self.event.finish - self.event.start
      self.event.start, self.event.finish = start, start + delta
      self._eventChanged()
    else:
      self._send(error)
  
  def _handleEnterFinishTime(self, text: str):
    try:
      self.event.finish = self.event.start + dt.timedelta(minutes=int(text))
      self._eventChanged()
    except:
      self._send('Нужно число! число минут! Как "120", например, или "150"')
  
  def _handleEnterPlace(self, text: str):
    self.event.place = Place(name=text)
    self._eventChanged()
  
  def _handleEnterUrl(self, text: str):
    if check_url(text):
      self.event.url = text
      self._eventChanged()
    else:
      self._send('Что-то не похоже на ссылку, давай по новой')
  
  def _handleEnterDesc(self, text: str):
    self.event.desc = text
    self._eventChanged()

  
  # OTHER
  def _translate(self):
    text = self._makeEventRepr()
    kwargs = {
      'chat_id': self.chatId,
      'text': self._makeEventRepr(),
      'reply_markup': self._makeMarkup(),
      'entities': [MessageEntity(
        type='code',
        offset=0,
        length=len(text),
      )]
    }
    if self.messageId is None:
      self.messageId = self.tg.send_message(**kwargs).message_id
    else:
      kwargs['message_id'] = self.messageId
      self.tg.edit_message_text(**kwargs)

  def _makeEventRepr(self) -> str:
    return (f'Название:   {self.event.desc}\n'
            f'Начало:     {self.event.start.strftime("%x %X")}\n'
            f'Конец:      {self.event.finish.strftime("%x %X")}\n'
            f'Место/Орг.: {self.event.place.name}\n'
            f'URL:        {self.event.url}')
  
  def _makeMarkup(self) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
      *[self._fieldToButton(f) for f in [EventField.DESC,
                                         EventField.START_TIME,
                                         EventField.FINISH_TIME]],
      row_width=3
    )
    markup.add(
      *[self._fieldToButton(f) for f in [EventField.PLACE,
                                         EventField.URL]],
      row_width=2
    )
    markup.add(
      InlineKeyboardButton('Завершить', callback_data=self._cd(EventTgEditor.EXIT)),
      row_width=1
    )
    return markup
    
  def _fieldToButton(self, field) -> InlineKeyboardButton:
    text = {
      EventField.START_TIME : 'Начало',
      EventField.FINISH_TIME : 'Длительность',
      EventField.PLACE : 'Место/Орг.',
      EventField.URL : 'Ссыль',
      EventField.DESC : 'Название',
    }[field]
    return InlineKeyboardButton(text, callback_data=self._cd(field))
  
  def _cd(self, field):
    return f'{EventTgEditor.__name__}_{field}'
  
  def _send(self, message, answer_callback_query_id: int = None):
    self.tg.send_message(chat_id=self.chatId, text=message)
    if answer_callback_query_id is not None:
      self.tg.answer_callback_query(callback_query_id=answer_callback_query_id,
                                    text=message)

  def _eventChanged(self):
    self._send('Успех!')
    self.state = None
    self._translate()
    if self.onEdit is not None:
      self.onEdit()

  def _finish(self):
    self.clear()
    if self.onFinish is not None:
      self.onFinish()
    