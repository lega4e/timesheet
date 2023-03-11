import re

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import MenuButtonCommands, CallbackQuery
from typing import Optional, Any

from src.entities.event.event import Event
from src.entities.event.event_factory import EventFactory
from src.entities.event.event_repository import EventRepository
from src.entities.event.event_tg_editor import EventTgEditor
from src.entities.event.event_tg_maker import EventTgMaker
from src.entities.message_maker.accessory import send_message
from src.entities.message_maker.emoji import Emoji
from src.entities.message_maker.message_maker import MessageMaker
from src.entities.message_maker.piece import Piece
from src.entities.timesheet.timesheet import Timesheet
from src.entities.timesheet.timesheet_repository import TimesheetRepository
from src.entities.translation.translation_factory import TranslationFactory
from src.entities.translation.translation_repository import TranslationRepo
from src.utils.logger.logger import FLogger
from src.utils.notifier import Notifier
from src.utils.utils import insert_between, reduce_list


class UserState:
  FREE = 'FREE'
  CREATING_EVENT = 'CREATING_EVENT'
  EDITING_EVENT = 'EDITING_EVENT'
  ENTER_TIMESHEET_HEAD = 'ENTER_TIMESHEET_HEAD'
  ENTER_TIMESHEET_TAIL = 'ENTER_TIMESHEET_TAIL'


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
    message = self.msgMaker.help()
    self.send(message=message)


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
    if len(events) == 0:
      self.send('Пусто :(', fail=True)
    else:
      self.send('\n'.join([MessageMaker.eventPreview(e) for e in events]))

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
    self.send('Мероприятие успешно удалено', ok=True)


  # timesheet commands
  def handleMakeTimesheet(self, text: str = None):
    self._checkAndMakeFree()
    name, pswd = self._logpassCheck(text)
    if name is None or pswd is None:
      return
    timesheets = [tm[1]
                  for tm in self.timesheetRepository.timesheets.values()
                  if tm[1].name == name]
    if len(timesheets) != 0:
      self.send([Piece('Расписание с именем '),
                 Piece(f'{name}', type='code'),
                 Piece(' уже есть :( давай по новой')],
                fail=True)
      return
    self.timesheetId = self.timesheetRepository.create(name=name,pswd=pswd).id
    self.send([Piece('Расписание '),
               Piece(f'{name}', type='code'),
               Piece(' с паролем '),
               Piece(f'{pswd}', type='code'),
               Piece(' успешно создано')],
              ok=True)
    self.notify()
    
  def handleSetTimesheet(self, text: str = None):
    self._checkAndMakeFree()
    name, pswd = self._logpassCheck(text)
    if name is None or pswd is None:
      return
    timesheets = [tm[1]
                  for tm in self.timesheetRepository.timesheets.values()
                  if tm[1].name == name]
    if len(timesheets) == 0:
      self.send([Piece('Расписание с названием '),
                 Piece(f'{name}', type='code'),
                 Piece(' не найдено :(')],
                fail=True)
      return
    if pswd != timesheets[0].password:
      self.send('Пароль не подходит :(', fail=True)
      return
    self.timesheetId = timesheets[0].id
    self.send([Piece('Успешно выбрано расписание '),
               Piece(f'{name}', type='code')],
              ok=True)
    self.notify()

  def handleSetTimesheetHead(self):
    self._checkAndMakeFree()
    if not self._checkTimesheet():
      return
    self.state = UserState.ENTER_TIMESHEET_HEAD
    self.send('Введите заголовок расписания', edit=True)

  def handleSetTimesheetTail(self):
    self._checkAndMakeFree()
    if not self._checkTimesheet():
      return
    self.state = UserState.ENTER_TIMESHEET_TAIL
    self.send('Введите подвал расписания', edit=True)

  def handleShowTimesheetInfo(self):
    self._checkAndMakeFree()
    if not self._checkTimesheet():
      return
    self.send([Piece(f'Название: "{self._findTimesheet().name}"\n'
                     f'Пароль:   "{self._findTimesheet().password}"',
                     type='code')])

  def handleShowTimesheetList(self):
    self._checkAndMakeFree()
    names = [tm.name for _, tm in self.timesheetRepository.timesheets.values()]
    self.send(
      [Piece('Существующие расписания:\n')] +
      reduce_list(
        lambda a, b: a + b,
        insert_between(
          [[Piece(f'{Emoji.TIMESHEET_ITEM} '), Piece(f'{name}', type='code')]
           for name in names],
          [Piece('\n')],
        ),
        [],
      )
    )


  # post commands
  def handleSetChannel(self, text):
    self._checkAndMakeFree()
    m = re.match(r'(https?://)?t\.me/(\w+)', text)
    if m is not None:
      channel = '@' + m.group(2)
    else:
      m = re.match(r'@?(\w+)', text)
      if m is not None:
        channel = '@' + m.group(1)
      else:
        self.send([Piece('Аргументом нужно добавить идентификатор (логин) канала вида '),
                   Piece('@xxx', type='code'),
                   Piece(' или ссылку на канал: '),
                   Piece('/set_channel <логин или ссылка>', type='code')],
                  warning=True)
        return
    self.channel = channel
    self.send(f'Канал успешно установлен на {self.channel}', ok=True)
    self.notify()
  
  def handlePost(self):
    message = self._makePost()
    if message is not None:
      self.post(message)
    
  def handlePostPreview(self):
    message = self._makePost()
    if message is not None:
      self.send(message)

  # translate commands
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
        self.send('Успешно добавили трансляцию', ok=True)
      else:
        self._sendPostFail()
      return
    channel = self.channel
    m = re.match(r'(https?://)?t\.me/(\w+)/(\d+)', text)
    if m is not None:
      channel = '@' + m.group(2)
      message_id = int(m.group(3))
    else:
      m = re.match(r'\d+', text)
      if m is not None:
        message_id = int(m.group(0))
      else:
        self.send('ID сообщения — это просто число или ссылка на пост!!', warning=True)
        return
    print(channel, message_id)
    tr = self.translationFactory.make(
      chat_id=channel,
      timesheet_id=self.timesheetId,
      message_id=message_id
    )
    if self.translationRepo.add(tr) and tr.updatePost():
      self.send('Успешно добавили трансляцию в сообщение '
                f'https://t.me/{channel[1:]}/{message_id}',
                ok=True)
    else:
      self.send('Что-то пошло не так :(', fail=True)
    
  def handleClearTranslations(self):
    self._checkAndMakeFree()
    if not self._checkTimesheet() or not self._checkChannel():
      return
    self.translationRepo.removeTranslations(
      lambda tr: tr.chatId == self.channel or tr.chatId is None
    )
    self.send('Успешно удалили все трансляции для выбранного канала', ok=True)


  # other handlers
  def handleText(self, text: str):
    if self.state == UserState.FREE:
      self.send('Непонятно.. что ты хочешь..? напиши /help', fail=True)
    elif self.state == UserState.CREATING_EVENT:
      self.eventTgMaker.handleText(text)
    elif self.state == UserState.EDITING_EVENT:
      self.eventTgEditor.handleText(text)
    elif self.state == UserState.ENTER_TIMESHEET_HEAD:
      self.state = UserState.FREE
      if not self._checkTimesheet():
        return
      self._findTimesheet().setHead(
        [Piece(text)] if text.lower() != 'none' else None
      )
      self.send('Заголовок расписания успешно установлен!', ok=True)
    elif self.state == UserState.ENTER_TIMESHEET_TAIL:
      self.state = UserState.FREE
      if not self._checkTimesheet():
        return
      self._findTimesheet().setTail(
        [Piece(text)] if text.lower() != 'none' else None
      )
      self.send('Подвал расписания успешно установлен!', ok=True)
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
  def send(
    self,
    message,
    disable_web_page_preview=True,
    edit=False,
    warning=False,
    ok=False,
    fail=False,
  ):
    send_message(
      tg=self.tg,
      chat_id=self.chat,
      message=message,
      disable_web_page_preview=disable_web_page_preview,
      edit=edit,
      warning=warning,
      ok=ok,
      fail=fail,
    )
    
  def post(self, message, disable_web_page_preview=True):
    if not self._checkChannel():
      return
    try:
      send_message(
        tg=self.tg,
        chat_id=self.channel,
        message=message,
        disable_web_page_preview=disable_web_page_preview,
      )
      self.send('Пост успешно сделан!', ok=True)
    except ApiTelegramException as e:
      self._sendPostFail(e)

    
  # private
  def _onEventCreated(self, event: Event):
    self.state = UserState.FREE
    timesheet = self._findTimesheet()
    if timesheet is None:
      self.send('Расписание куда-то делось.. мероприятие не добавлено :(', fail=True)
      return
    self.eventRepository.add(event)
    timesheet.addEvent(event.id)
    self.send(f'Мероприятие #{event.id} успешно добавлено в расписание!', ok=True)
    
  def _onEventEditorFinish(self):
    self.state = UserState.FREE
    
  def _checkAndMakeFree(self) -> bool:
    if self.state == UserState.FREE:
      return True
    elif self.state == UserState.EDITING_EVENT:
      self.send('Редактирование события завершено', ok=True)
    elif self.state == UserState.CREATING_EVENT:
      self.send('Создание события прервано', warning=True)
    elif self.state == UserState.ENTER_TIMESHEET_HEAD:
      self.send('Ввод заголовка расписания прервано', warning=True)
    elif self.state == UserState.ENTER_TIMESHEET_TAIL:
      self.send('Ввод подвала расписания прервано', warning=True)
    self.state = UserState.FREE
    return False
  
  def _checkTimesheet(self) -> bool:
    if self.timesheetId is None:
      self.send('Вы не подключены ни к какому расписанию', warning=True)
      return False
    if self._findTimesheet() is None:
      self.send('Расписание не найдено :( возможно, его удалили', fail=True)
      return False
    return True
  
  def _checkChannel(self) -> bool:
    if self.channel is None:
      self.send('Ошибкочка: канал не установлен, используйте /set_channel, '
                'чтобы установить канал', warning=True)
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
                  'Используйте /show_events, чтобы посмотреть события',
                  warning=True)
        return None
      return events[0]
    except:
      self.send('Введите корректный id (см. /show_events)', warning=True)
      return None
    
  def _sendPostFail(self, e = None):
    self.send(f'Произошла ошибка при попытке сделать пост :(\n\n'
              f'Возможные причины таковы:\n'
              f'1) Не верно указано название канала (сейчас: {self.channel})\n'
              f'2) Бот не является администратором канала' +
              ('' if e is None else
              f'\n\nВот как выглядит сообщение об ошибки: {e}'),
              warning=True)
    
  def _makePost(self) -> [Piece]:
    self._checkAndMakeFree()
    if not self._checkTimesheet():
      return None
    timesheet = self._findTimesheet()
    events = list(timesheet.events())
    if len(events) == 0:
      self.send('Нельзя запостить пустое расписание', warning=True)
      return None
    return self.msgMaker.timesheetPost(events,
                                       head=timesheet.head,
                                       tail=timesheet.tail)
  
  def _logpassCheck(self, text) -> (str, str):
    words = list(text.split())
    if (len(words) != 2
      or re.match(r'^\w+$', words[0]) is None
      or re.match(r'^\w+$', words[1]) is None):
      self.send('Неее. Нужно ввести только название и пароль; они могут'
                'состоять только из латинских букв, цифр и символов'
                'нижнего подчёркивания', warning=True)
      return None, None
    return words[0], words[1]

