import datetime as dt
import re
import time

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import MessageEntity, MenuButton, MenuButtonCommands, CallbackQuery
from typing import Optional, Any

from src.entities.event.event import Event
from src.entities.event.event_factory import EventFactory
from src.entities.event.event_repository import EventRepository
from src.entities.event.event_tg_editor import EventTgEditor
from src.entities.event.event_tg_maker import EventTgMaker
from src.entities.message_maker.message_maker import MessageMaker
from src.entities.timesheet.timesheet import Timesheet
from src.entities.timesheet.timesheet_repository import TimesheetRepository
from src.entities.translation.translation_factory import TranslationFactory
from src.entities.translation.translation_repository import TranslationRepo
from src.utils.logger.logger import FLogger
from src.utils.notifier import Notifier


class UserState:
  FREE = 'FREE'
  CREATING_EVENT = 'CREATING_EVENT'
  EDITING_EVENT = 'EDITING_EVENT'


class User(Notifier):
  def __init__(
    self,
    tg: TeleBot,
    msg_maker: MessageMaker,
    event_repository: EventRepository,
    event_factory: EventFactory,
    timesheet_repository: TimesheetRepository,
    translation_factory: TranslationFactory,
    translation_repo: TranslationRepo,
    logger: FLogger,
    channel: str = None,
    chat: int = None,
    timesheet_id: int = None,
    serialized: {str : Any} = None,
  ):
    super().__init__()
    self.tg = tg
    self.msgMaker = msg_maker
    self.eventRepository = event_repository
    self.timesheetRepository = timesheet_repository
    self.translationFactory = translation_factory
    self.translationRepo = translation_repo
    self.logger = logger
    self.state = UserState.FREE
    if serialized is None:
      self.channel = channel
      self.chat = chat
      self.timesheetId = timesheet_id
    else:
      self.channel = serialized.get('channel')
      self.chat = serialized['chat']
      self.timesheetId = serialized['timesheet_id']
    self.eventTgMaker = EventTgMaker(
      tg=self.tg,
      event_factory=event_factory,
      chat=self.chat,
      on_created=self._onEventCreated,
    )
    self.eventTgEditor: Optional[EventTgEditor] = None
    self._setChatMenuButton()

  def serialize(self) -> {str : Any}:
    return {
      'channel': self.channel,
      'chat': self.chat,
      'timesheet_id': self.timesheetId,
    }
  
  
  # HANDLERS FOR TELEGRAM
  # common commands
  def handleStart(self):
    self._checkAndMakeFree()
    self.send('Приветствуют тебя, мастер, заведующий расписанием!')

  def handleHelp(self):
    self._checkAndMakeFree()
    self.send(self.msgMaker.help())


  # event commands
  def handleMakeEvent(self):
    self._checkAndMakeFree()
    if not self._checkTimesheet():
      return
    self.state = UserState.CREATING_EVENT
    self.eventTgMaker.onStart()
  
  def handleShowEvents(self):
    self._checkAndMakeFree()
    if not self._checkTimesheet():
      return
    events = sorted(list(self._findTimesheet().events()),
                    key=lambda e: e.start)
    self.send('Пусто :('
              if len(events) == 0 else
              '\n'.join([MessageMaker.eventPreview(e) for e in events]))

  def handleEditEvent(self, text):
    self._checkAndMakeFree()
    event = self._checkFindEventByTextId(text)
    if event is None:
      return
    self.eventTgEditor = EventTgEditor(
      tg=self.tg,
      on_finish=self._onEventEditorFinish,
      on_edit_field=event.notify,
      event=event,
      chat_id=self.chat,
    )
    self.state = UserState.EDITING_EVENT
    self.eventTgEditor.onStart()

  def handleRemoveEvent(self, text):
    self._checkAndMakeFree()
    event = self._checkFindEventByTextId(text)
    if event is None:
      return
    timesheet = self.timesheetRepository.find(self.timesheetId)
    timesheet.removeEvent(event.id)
    self.eventRepository.remove(event.id)
    self.send('Мероприятие успешно удалено')


  # timesheet commands
  def handleMakeTimesheet(self, text: str = None):
    self._checkAndMakeFree()
    if text is None or text == '':
      self.send('Нужно ввести название')
      return
    self.timesheetId = self.timesheetRepository.create(name=text).id
    self.notify()
    self.send(f'Расписание "{text}" успешно создано')
    
  def handleSetTimesheet(self, text: str = None):
    self._checkAndMakeFree()
    if text is None or text == '':
      self.send('Нужно ввести название расписания, к которому вы хотите подключиться')
      return
    timesheets = [tm[1]
                  for tm in self.timesheetRepository.timesheets.values()
                  if tm[1].name == text]
    if len(timesheets) == 0:
      self.send('Расписания с таким названием не найдено :(')
      return
    self.timesheetId = timesheets[0].id
    self.notify()
    self.send(f'Успешно выбрано расписание {text}')


  # post commands
  def handleSetChannel(self, text):
    self._checkAndMakeFree()
    channel = None
    m = re.match(r'@?(\w+)', text)
    if m is not None:
      channel = '@' + m.group(1)
    else:
      m = re.match(r'(https?://)?t\.me/(\w+)', text)
      if m is not None:
        channel = '@' + m.group(2)
      else:
        self.send('Нужно ввести идентификатор (логин) канала вида @xxx или ссылку на канал')
        return
    self.channel = channel
    self.send(f'Канал успешно установлен на "{self.channel}"')
    self.notify()
  
  def handlePost(self):
    self._checkAndMakeFree()
    if not self._checkTimesheet():
      return
    events = list(self._findTimesheet().events())
    if len(events) == 0:
      self.send('Нельзя запостить пустое расписание')
      return
    message, entities = self.msgMaker.timesheetPost(events)
    self.post(message, entities=entities)
    
  def handleTranslate(self, text):
    self._checkAndMakeFree()
    if not self._checkTimesheet() or not self._checkChannel():
      return
    if text == '':
      tr = self.translationFactory.make(
        chat_id=self.channel,
        timesheet_id=self.timesheetId,
      )
      if self.translationRepo.add(tr):
        self.send('Успешно добавили трансляцию')
      else:
        self._sendPostFail()
      return
    exprs = [
      r'https?://t\.me/[\w_]+/(\d+)',
      r'(\d+)',
    ]
    message_id = None
    for expr in exprs:
      m = re.match(expr, text)
      if m is not None:
        message_id = int(m.group(1))
    if message_id is None:
      self.send('ID сообщения — это просто число или ссылка на пост!!')
      return
    tr = self.translationFactory.make(
      chat_id=self.channel,
      timesheet_id=self.timesheetId,
      message_id=message_id
    )
    if self.translationRepo.add(tr) and tr.updatePost():
      self.send('Успешно добавили трансляцию в сообщение '
                f'https://t.me/{self.channel[1:]}/{message_id}')
    else:
      self.send('Что-то пошло не так :(')
    
  def handleClearTranslations(self):
    self._checkAndMakeFree()
    if not self._checkTimesheet() or not self._checkChannel():
      return
    self.translationRepo.removeTranslations(
      lambda tr: tr.chatId == self.channel or tr.chatId is None
    )
    self.send('Успешно удалили все трансляции для выбранного канала')


  # other handlers
  def handleText(self, text: str):
    if self.state == UserState.FREE:
      self.send('Непонятно, что ты хочешь..? напиши /help')
    elif self.state == UserState.CREATING_EVENT:
      self.eventTgMaker.handleText(text)
    elif self.state == UserState.EDITING_EVENT:
      self.eventTgEditor.handleText(text)
    else:
      raise Exception(f'No switch case for {self.state}')
    
    
  # CALLBACK QUERY
  def callbackQuery(self, call: CallbackQuery):
    if self.state == UserState.FREE:
      self.tg.answer_callback_query(call.id, text='Непонятно..')
    elif self.state == UserState.CREATING_EVENT:
      self.eventTgMaker.callbackQuery(call)
    elif self.state == UserState.EDITING_EVENT:
      self.eventTgEditor.callbackQuery(call)


  # OTHER
  def send(self, message, disable_web_page_preview=True):
    # self.logger.answer(chat_id=self.chat, text=message)
    self.tg.send_message(
      chat_id=self.chat,
      text=message,
      disable_web_page_preview=disable_web_page_preview,
    )
    
  def post(self, message, entities=None, disable_web_page_preview=True):
    if not self._checkChannel():
      return
    try:
      self.tg.send_message(
        self.channel,
        message,
        entities=entities,
        disable_web_page_preview=disable_web_page_preview,
      )
      self.send('Пост успешно сделан!')
    except ApiTelegramException:
      self._sendPostFail()

    
  # private
  def _onEventCreated(self, event: Event):
    self.state = UserState.FREE
    timesheet = self._findTimesheet()
    if timesheet is None:
      self.send('Расписание куда-то делось.. мероприятие не добавлено :(')
      return
    self.eventRepository.add(event)
    timesheet.addEvent(event.id)
    self.send('Мероприятие успешно добавлено в расписание!')
    
  def _onEventEditorFinish(self):
    self.state = UserState.FREE
    
  def _checkAndMakeFree(self) -> bool:
    if self.state == UserState.FREE:
      return True
    elif self.state == UserState.EDITING_EVENT:
      self.send('Редактирование события завершено')
    elif self.state == UserState.CREATING_EVENT:
      self.send('Создание события прервано')
    self.state = UserState.FREE
    return False
  
  def _checkTimesheet(self) -> bool:
    if self.timesheetId is None:
      self.send('Вы не подключены ни к какому расписанию')
      return False
    if self._findTimesheet() is None:
      self.send('Расписание не найдено :( возможно, его удалили')
      return False
    return True
  
  def _checkChannel(self) -> bool:
    if self.channel is None:
      self.send('Ошибкочка: канал не установлен, используйте /set_channel, чтобы установить канал')
      return False
    return True


  def _findTimesheet(self) -> Optional[Timesheet]:
    return (None
            if self.timesheetId is None else
            self.timesheetRepository.find(self.timesheetId))
  
  def _setChatMenuButton(self):
    self.tg.set_chat_menu_button(
      chat_id=self.chat,
      menu_button=MenuButtonCommands(type='commands'),
    )
    
  def _checkFindEventByTextId(self, text) -> Optional[Event]:
    try:
      id = int(text)
      if not self._checkTimesheet():
        return None
      timesheet = self.timesheetRepository.find(self.timesheetId)
      events = list(timesheet.events(predicat=lambda e: e.id == id))
      
      if len(events) == 0:
        self.send('Мероприятия с таким id не найдено. '
                  'Используйте /show_events, чтобы посмотреть события')
        return None
      return events[0]
    except:
      self.send('Введите корректный id (см. /show_events)')
      return None
    
  def _sendPostFail(self):
    self.send(f'\u26A0 Произошла ошибка при попытке сделать пост :(\n\n'
              f'Возможные причины таковы:\n'
              f'1) Не верно указано название канала (сейчас: {self.channel})\n'
              f'2) Бот не является администратором канала\n\n'
              f'Вот как выглядит сообщение об ошибки: {e}')
