import re

from telebot import TeleBot
from telebot.types import ReplyKeyboardRemove, CallbackQuery

from src.entities.event.accessory import *
from src.entities.event.event import Event, Place
from src.entities.event.event_factory import EventFactory
from src.entities.event.event_fields_parser import *


class EventTgMakerState:
  ENTER_START_TIME = 'ENTER_START_TIME'
  ENTER_FINISH_TIME = 'ENTER_FINISH_TIME'
  ENTER_PLACE = 'ENTER_PLACE'
  ENTER_URL = 'ENTER_URL'
  ENTER_DESC = 'ENTER_DESC'

  list = [
    ENTER_DESC,
    ENTER_START_TIME,
    ENTER_FINISH_TIME,
    ENTER_PLACE,
    ENTER_URL,
  ]
  
  @staticmethod
  def nextState(state):
    index = EventTgMakerState.list.index(state)
    if index + 1 < len(EventTgMakerState.list):
      return EventTgMakerState.list[index + 1]
    else:
      return None


class EventTgMaker:
  PASS_URL = 'PASS_URL'
  
  def __init__(
    self,
    tg: TeleBot,
    event_factory: EventFactory,
    chat: int,
    on_created = None
  ):
    self.tg = tg
    self.eventFactory = event_factory
    self.chat = chat
    self.onCreated = on_created
    self.proto = Event()
    self.state = None
    self.clear()
    
  def clear(self):
    self.state = EventTgMakerState.list[0]
    self.proto = Event()
    
  def onStart(self):
    self._send('Создаём мероприятие!!!')
    self._executeBeforeState()
  
  def handleText(self, text):
    {
      EventTgMakerState.ENTER_START_TIME : self._handleEnterStartTime,
      EventTgMakerState.ENTER_FINISH_TIME : self._handleEnterFinishTime,
      EventTgMakerState.ENTER_PLACE : self._handleEnterPlace,
      EventTgMakerState.ENTER_URL : self._handleEnterUrl,
      EventTgMakerState.ENTER_DESC : self._handleEnterDesc,
    }[self.state](text)
    
  def callbackQuery(self, call: CallbackQuery):
    if self.state == EventTgMakerState.ENTER_PLACE:
      self._callbackQueryEnterPlace(call)
    elif self.state == EventTgMakerState.ENTER_URL and call.data == EventTgMaker.PASS_URL:
      self._callbackQueryEnterUrl(call)
    else:
      self.tg.answer_callback_query(call.id, 'Недоумеваю..')

  def _nextState(self):
    self.state = EventTgMakerState.nextState(self.state)
    if self.state is not None:
      self._executeBeforeState()
    else:
      self._send('Мероприятие создано!')
      if self.onCreated is not None:
        self.onCreated(
          self.eventFactory.make(
            start=self.proto.start,
            finish=self.proto.finish,
            place=self.proto.place,
            url=self.proto.url,
            desc=self.proto.desc,
            creator=self.chat,
          )
        )
      self.clear()

  def _executeBeforeState(self):
    {
      EventTgMakerState.ENTER_START_TIME : self._beforeEnterStartTime,
      EventTgMakerState.ENTER_FINISH_TIME : self._beforeEnterFinishTime,
      EventTgMakerState.ENTER_PLACE : self._beforeEnterPlace,
      EventTgMakerState.ENTER_URL : self._beforeEnterUrl,
      EventTgMakerState.ENTER_DESC : self._beforeEnterDesc,
    }[self.state]()

  def _beforeEnterStartTime(self):
    self._send('Введите дату и время начала мероприятия')

  def _beforeEnterFinishTime(self):
    self._send('Введите продолжительность мероприятия (в минутах)')

  def _beforeEnterPlace(self):
    self.tg.send_message(
      chat_id=self.chat,
      text='Введите или выберите место проведения мероприятия',
      reply_markup=place_markup(),
    )

  def _beforeEnterUrl(self):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Пропустить', callback_data=EventTgMaker.PASS_URL))
    self.tg.send_message(
      chat_id=self.chat,
      text='Введите ссылку на пост мероприятия',
      reply_markup=markup,
    )

  def _beforeEnterDesc(self):
    self._send('Введите название мероприятия')

  def _handleEnterStartTime(self, text: str):
    self.proto.start, error = parse_datetime(text)
    if self.proto.start is not None:
      self.proto.start = correct_datetime(self.proto.start,
                                          isfuture=True,
                                          delta=dt.timedelta(weeks=4))
      self._nextState()
    else:
      self._send(error)

  def _handleEnterFinishTime(self, text: str):
    try:
      self.proto.finish = self.proto.start + dt.timedelta(minutes=int(text))
      self._nextState()
    except:
      self._send('Нужно число! число минут! Как "120", например, или "150"')

  def _handleEnterPlace(self, text: str):
    self.proto.place = Place(name=text)
    self._nextState()

  def _handleEnterUrl(self, text: str):
    if text.lower() in ['пропустить', 'пропуск']:
      self.proto.url = None
      self._nextState()
    elif check_url(text):
      self.proto.url = text
      self._nextState()
    else:
      self._send('Что-то не похоже на ссылку, давай по новой')

  def _handleEnterDesc(self, text: str):
    self.proto.desc = text
    self._nextState()

  def _callbackQueryEnterUrl(self, call):
    self.tg.answer_callback_query(call.id, 'Ввод URL пропущен')
    self.proto.url = None
    self._send('URL не введён, ну и ладно')
    self._nextState()

  def _callbackQueryEnterPlace(self, call):
    self.proto.place = Place(name=place_to_str_map().get(call.data))
    if self.proto.place.name is None:
      self.tg.answer_callback_query(call.id, 'Что-то не так :(')
      return
    self.tg.answer_callback_query(call.id, self.proto.place.name)
    self._send(f'Место мероприятия установлено: {self.proto.place.name}')
    self._nextState()

  def _send(self, message):
    self.tg.send_message(chat_id=self.chat, text=message)

