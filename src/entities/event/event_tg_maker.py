import datetime as dt
import re

from telebot import TeleBot

from src.entities.event.event import Event, Place
from src.entities.event.event_factory import EventFactory


class EventTgMakerState:
  ENTER_START_TIME = 'ENTER_START_TIME'
  ENTER_FINISH_TIME = 'ENTER_FINISH_TIME'
  ENTER_PLACE = 'ENTER_PLACE'
  ENTER_URL = 'ENTER_URL'
  ENTER_DESC = 'ENTER_DESC'
  
  _list = [
    ENTER_START_TIME,
    ENTER_FINISH_TIME,
    ENTER_PLACE,
    ENTER_URL,
    ENTER_DESC,
  ]
  
  @staticmethod
  def nextState(state):
    index = EventTgMakerState._list.index(state)
    if index + 1 < len(EventTgMakerState._list):
      return EventTgMakerState._list[index + 1]
    else:
      return None


class EventTgMaker:
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
    self.state = EventTgMakerState.ENTER_START_TIME
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
  
  def _nextState(self):
    self.state = EventTgMakerState.nextState(self.state)
    if self.state is not None:
      self._executeBeforeState()
    else:
      self.state = EventTgMakerState.ENTER_START_TIME
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
    self._send('Введите дату и время окончания мероприятия')

  def _beforeEnterPlace(self):
    self._send('Введите место проведения мероприятия')

  def _beforeEnterUrl(self):
    self._send('Введите ссылку на пост мероприятия')

  def _beforeEnterDesc(self):
    self._send('Введите описание мероприятия')

  def _handleEnterStartTime(self, text: str):
    try:
      self.proto.start = dt.datetime.strptime(text, '%d.%m.%Y %H:%M')
      self._nextState()
    except Exception as e:
      print(e)
      self._send('Не получилось распарсить, давай по новой')

  def _handleEnterFinishTime(self, text: str):
    try:
      self.proto.finish = dt.datetime.strptime(text, '%d.%m.%Y %H:%M')
      self._nextState()
    except:
      self._send('Не получилось распарсить, давай по новой')

  def _handleEnterPlace(self, text: str):
    self.proto.place = Place(name=text)
    self._nextState()

  def _handleEnterUrl(self, text: str):
    if re.match(r'^https?://.*\..+$', text):
      self.proto.url = text
      self._nextState()
    else:
      self._send('Что-то не похоже на ссылку, давай по новой')

  def _handleEnterDesc(self, text: str):
    self.proto.desc = text
    self._nextState()

  def _send(self, message):
    self.tg.send_message(chat_id=self.chat, text=message)
