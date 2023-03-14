from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import CallbackQuery
from typing import Optional, Any

from src.domain.locator import LocatorStorage, Locator
from src.entities.event.event import Place
from src.entities.event.event_factory import EventFactory
from src.entities.event.event_fields_parser import datetime_today
from src.entities.event.event_repository import EventRepository
from src.entities.event.event_tg_maker import TgEventInputFieldsConstructor
from src.entities.message_maker.accessory import send_message
from src.entities.message_maker.emoji import Emoji
from src.entities.message_maker.message_maker import MessageMaker
from src.entities.timesheet.timesheet import Timesheet
from src.entities.timesheet.timesheet_repository import TimesheetRepo
from src.entities.translation.translation_factory import TranslationFactory
from src.entities.translation.translation_repository import TranslationRepo
from src.utils.logger.logger import FLogger
from src.utils.notifier import Notifier
from src.utils.serialize import Serializable
from src.utils.tg.tg_input_field import TgInputField
from src.utils.tg.tg_input_form import TgInputForm
from src.utils.tg.tg_state import TgState
from src.utils.tg.tg_state_branch import TgStateBranch, BranchButton
from src.utils.tg.value_validators import *
from src.utils.utils import insert_between, reduce_list


class User(Notifier, TgState, Serializable, LocatorStorage):
  def __init__(
    self,
    locator: Locator,
    channel: str = None,
    chat: int = None,
    timesheet_id: int = None,
    serialized: {str : Any} = None,
  ):
    Notifier.__init__(self)
    TgState.__init__(self)
    LocatorStorage.__init__(self, locator)
    self.tg: TeleBot = self.locator.tg()
    self.msgMaker: MessageMaker = self.locator.messageMaker()
    self.eventRepository: EventRepository = self.locator.eventRepository()
    self.eventFactory: EventFactory = self.locator.eventFactory()
    self.timesheetRepository: TimesheetRepo = self.locator.timesheetRepo()
    self.translationFactory: TranslationFactory = self.locator.translationFactory()
    self.translationRepo: TranslationRepo = self.locator.translationRepo()
    self.logger: FLogger = self.locator.flogger()
    self.tgState = None
    if serialized is not None:
      self.deserialize(serialized)
    else:
      self.channel = channel
      self.chat = chat
      self.timesheetId = timesheet_id
    
    
  # OVERRIDE METHODS
  def _onTerminate(self):
    pass

  def _handleMessage(self, m: Message):
    self.send('Непонятно.. что ты хочешь..? напиши /help', emoji='fail')
    
  def _handleMessageBefore(self, m: Message) -> bool:
    if m.text[0] == '/':
      self.terminateSubstate()
      self.send('Неизвестная команда..', emoji='fail')
      return True
    return False

  def _handleCallbackQuery(self, q: CallbackQuery):
    self.tg.answer_callback_query(q.id, text='Непонятно..')

  def serialize(self) -> {str : Any}:
    return {
      'channel': self.channel,
      'chat': self.chat,
      'timesheet_id': self.timesheetId,
    }
    
  def deserialize(self, serialized: {str: Any}):
    self.channel = serialized.get('channel')
    self.chat = serialized.get('chat')
    self.timesheetId = serialized.get('timesheet_id')


  # HANDLERS FOR TELEGRAM
  # common commands
  def handleStart(self):
    self.terminateSubstate()
    self.send('Приветствуют тебя, мастер, заведующий расписанием!')

  def handleHelp(self):
    self.terminateSubstate()
    self.send(message=self.msgMaker.help())


  # event commands
  def handleMakeEvent(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    
    def on_form_entered(data: []):
      event = self.eventFactory.make(desc=data[0],
                                     start=data[1],
                                     finish=None,
                                     place=Place(data[2]),
                                     url=data[3])
      self.eventRepository.add(event)
      self.findTimesheet().addEvent(event.id)
      self.send(f'Мероприятие #{event.id} успешно добавлено в расписание!', emoji='ok')
      self.resetTgState()

    constructor = TgEventInputFieldsConstructor(tg=self.tg, chat=self.chat)
    self.setTgState(TgInputForm(
      tg=self.tg,
      chat=self.chat,
      terminate_message='Создание мероприятия преравно',
      on_form_entered=on_form_entered,
      fields=[constructor.make_name_input_field(lambda _: True),
              constructor.make_datetime_input_field(lambda _: True),
              constructor.make_place_input_field(lambda _: True),
              constructor.make_url_input_field(lambda _: True)]
    ))

  def handleEditEvent(self):
    def on_field_entered(data):
      event = list(self.findTimesheet().events(lambda e: e.id == data))[0]
      state = None
      
      def on_event_field_entered(value, field_name: str):
        print(value, field_name)
        if field_name == 'name':
          event.desc = value
        elif field_name == 'start':
          event.start = value
        elif field_name == 'place':
          event.place.name = value
        elif field_name == 'url':
          event.url = value
        self.send('Успех!', emoji='ok')
        state.updateMessage()
        state.resetTgState()
        event.notify()

      def complete():
        self.send('Редактирование мероприятия завершено', emoji='ok')
        self.resetTgState()
      
      constructor = TgEventInputFieldsConstructor(tg=self.tg, chat=self.chat)
      state = TgStateBranch(
        tg=self.tg,
        chat=self.chat,
        make_buttons=lambda: [
          [BranchButton(
             'Название',
             constructor.make_name_input_field(
               lambda value: on_event_field_entered(value, 'name')
             )
           ),
           BranchButton(
             'Начало',
             constructor.make_datetime_input_field(
               lambda value: on_event_field_entered(value, 'start')
             )
           )],
          [BranchButton(
             'Место/Орг.',
             constructor.make_place_input_field(
               lambda value: on_event_field_entered(value, 'place')
             )
           ),
           BranchButton(
             'Ссыль',
             constructor.make_url_input_field(
               lambda value: on_event_field_entered(value, 'url')
             )
           )],
          [BranchButton('Завершить', action=complete, callback_answer='Завершено')],
        ],
        make_message=lambda: [
          Piece(f'Название:   {event.desc}\n'
                f'Начало:     {event.start.strftime("%x %X")}\n'
                f'Место/Орг.: {event.place.name}\n'
                f'URL:        {event.url}',
                type='code')
        ],
        on_terminate=lambda: self.send('Редактирование мероприятия заверщено', emoji='ok')
      )
      self.setTgState(state)

    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите ID мероприятия',
      terminate_message='Прервано редактирование мероприятия',
      on_field_entered=on_field_entered,
      validator=ChainValidator([
        IntValidator(error='ID — это просто число, его можно посмотреть командой /show_events'),
        FunctionValidator(self._eventIdFoundValidator),
      ]),
    ))
    
  def handleShowEvents(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    events = sorted(list(self.findTimesheet().events()),
                    key=lambda e: e.start)
    if len(events) == 0:
      self.send('Пусто :(', emoji='fail')
    else:
      self.send('\n'.join([MessageMaker.eventPreview(e) for e in events]))

  def handleRemoveEvent(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    
    def on_field_entered(data):
      timesheet = self.timesheetRepository.find(self.timesheetId)
      timesheet.removeEvent(id=data)
      self.eventRepository.remove(id=data)
      self.send('Мероприятие успешно удалено', emoji='ok')
      self.resetTgState()

    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите ID мероприятия',
      terminate_message='Прервано удаление мероприятия',
      on_field_entered=on_field_entered,
      validator=ChainValidator([
        IntValidator(error='ID — это просто число, его можно посмотреть командой /show_events'),
        FunctionValidator(self._eventIdFoundValidator),
      ]),
    ))


  # timesheet commands
  def handleMakeTimesheet(self):
    def name_validator(o: ValidatorObject):
      timesheet = self.timesheetRepository.findByName(o.data)
      if timesheet is not None:
        o.success = False
        o.error = [Piece('Расписание с именем '),
                   Piece(f'{o.data}', type='code'),
                   Piece(' уже есть :( давай по новой')]
        o.emoji = 'fail'
      return o
    
    def on_form_entered(data: []):
      name = data[0]
      pswd = data[1]
      self.timesheetId = self.timesheetRepository.create(name=name,pswd=pswd).id
      self.send([Piece('Расписание '),
                 Piece(f'{name}', type='code'),
                 Piece(' с паролем '),
                 Piece(f'{pswd}', type='code'),
                 Piece(' успешно создано')],
                emoji='ok')
      self.resetTgState()
      self.notify()
    
    self.terminateSubstate()
    self.setTgState(TgInputForm(
      tg=self.tg,
      chat=self.chat,
      terminate_message='Создание расписания преравно',
      on_form_entered=on_form_entered,
      fields=[
        TgInputField(
          tg=self.tg,
          chat=self.chat,
          greeting='Введите название',
          validator=ChainValidator(validators=[
            IdValidator(error=IdValidator.NAME_ERROR_MESSAGE),
            FunctionValidator(name_validator),
          ]),
          on_field_entered=lambda _: None,
        ),
        TgInputField(
          tg=self.tg,
          chat=self.chat,
          greeting='Введите пароль',
          validator=IdValidator(error=IdValidator.PSWD_ERROR_MESSAGE),
          on_field_entered=lambda _: None,
        )
      ]
    ))
    
  def handleSetTimesheet(self):
    tm = {}
    
    def name_validator(o: ValidatorObject):
      timesheet = self.timesheetRepository.findByName(o.data)
      if timesheet is None:
        o.success = False
        o.error = [Piece('Расписание с названием '),
                   Piece(f'{o.data}', type='code'),
                   Piece(' не найдено :( Существующие расписания '),
                   Piece('можно посмотреть командой /show_timesheet_list')]
        o.emoji = 'fail'
      elif timesheet.id == self.timesheetId:
        o.success = False
        o.error = 'Это расписание уже выбрано..'
        o.emoji = 'fail'
      else:
        tm['name'] = o.data
      return o
    
    def pswd_validator(o: ValidatorObject):
      timesheet = self.timesheetRepository.findByName(tm['name'])
      if timesheet.password != o.data:
        o.success = False
        o.error = 'Пароль не подходит'
        o.emoji = 'fail'
      return o
    
    def on_form_entered(data: []):
      timesheet = self.timesheetRepository.findByName(data[0])
      self.timesheetId = timesheet.id
      self.send([Piece('Успешно выбрано расписание '),
                 Piece(f'{data[0]}', type='code')],
                emoji='ok')
      self.resetTgState()
      self.notify()

    self.terminateSubstate()
    self.setTgState(TgInputForm(
      tg=self.tg,
      chat=self.chat,
      terminate_message='Выбор расписания прерван',
      on_form_entered=on_form_entered,
      fields=[
        TgInputField(
          tg=self.tg,
          chat=self.chat,
          greeting='Введите название расписания',
          validator=ChainValidator([
            IdValidator(error=IdValidator.NAME_ERROR_MESSAGE),
            FunctionValidator(name_validator),
          ]),
          on_field_entered=lambda _: None,
        ),
        TgInputField(
          tg=self.tg,
          chat=self.chat,
          greeting='Введите пароль',
          validator=ChainValidator([
            IdValidator(error=IdValidator.PSWD_ERROR_MESSAGE),
            FunctionValidator(pswd_validator),
          ]),
          on_field_entered=lambda _: None,
        ),
      ],
    ))
    
  def handleSetTimesheetHead(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    
    def on_entered(data):
      if not self._checkTimesheet():
        return
      self.findTimesheet().setHead(data)
      self.send('Заголовок успешно установлен!', emoji='ok')
      self.resetTgState()
      
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите заголовок расписания',
      on_field_entered=on_entered,
      validator=PieceValidator(),
      terminate_message='Ввод заголовка прерван',
    ))

  def handleSetTimesheetTail(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
  
    def on_entered(data):
      if not self._checkTimesheet():
        return
      self.findTimesheet().setTail(data)
      self.send('Подвал успешно установлен!', emoji='ok')
      self.resetTgState()
  
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите подвал расписания',
      on_field_entered=on_entered,
      validator=PieceValidator(),
      terminate_message='Ввод подвала прерван',
    ))

  def handleShowTimesheetInfo(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    self.send([Piece(f'Название: {self.findTimesheet().name}\n'
                     f'Пароль:   {self.findTimesheet().password}',
                     type='code')])

  def handleShowTimesheetList(self):
    self.terminateSubstate()
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
  def handleSetChannel(self):
    def on_field_entered(data: str):
      self.channel = data
      self.send(f'Канал успешно установлен на {self.channel}', emoji='ok')
      self.resetTgState()
      self.notify()

    self.terminateSubstate()
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите ссылку на канал',
      validator=TgPublicGroupOrChannelValidator(),
      terminate_message='Установка канала прервана',
      on_field_entered=on_field_entered,
    ))
  
  def handlePost(self):
    self.terminateSubstate()
    if not self._checkTimesheet() or not self._checkChannel():
      return
    message = self._makePost(lambda e: e.start >= datetime_today())
    if message is not None:
      self.post(message)
    
  def handlePostPreview(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    message = self._makePost(lambda e: e.start >= datetime_today())
    if message is not None:
      self.send(message)


  # translate commands
  def handleTranslate(self):
    self.terminateSubstate()
    if not self._checkTimesheet() or not self._checkChannel():
      return
    tr = self.translationFactory.make(
      chat_id=self.channel,
      timesheet_id=self.timesheetId,
    )
    if self.translationRepo.add(tr):
      self.send('Успешно добавили трансляцию', emoji='ok')
    else:
      self._sendPostFail()
    return
    
  def handleTranslateToMessage(self):
    def on_field_entered(data):
      tr = self.translationFactory.make(
        chat_id=data[0],
        timesheet_id=self.timesheetId,
        message_id=data[1]
      )
      if self.translationRepo.add(tr) and tr.updatePost():
        self.send('Успешно добавили трансляцию в сообщение '
                  f'https://t.me/{data[0][1:]}/{data[1]}',
                  emoji='ok')
      else:
        self.send('Что-то пошло не так..', emoji='fail')
      self.resetTgState()
  
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите ссылку на пост',
      validator=TgMessageUrlValidator(),
      terminate_message='Добавление трансляции прервано',
      on_field_entered=on_field_entered,
    ))
    
  def handleClearTranslations(self):
    self.terminateSubstate()
    if not self._checkTimesheet() or not self._checkChannel():
      return
    self.translationRepo.removeTranslations(
      lambda tr: tr.chatId == self.channel or tr.chatId is None
    )
    self.send('Успешно удалили все трансляции для выбранного канала', emoji='ok')


  # OTHER
  def send(self, message, emoji: str = None):
    send_message(
      tg=self.tg,
      chat_id=self.chat,
      text=message,
      disable_web_page_preview=True,
      emoji=emoji,
    )
    
  def post(self, message):
    try:
      send_message(
        tg=self.tg,
        chat_id=self.channel,
        text=message,
        disable_web_page_preview=True,
      )
      self.send('Пост успешно сделан!', emoji='ok')
    except ApiTelegramException as e:
      self._sendPostFail(e)

  def findTimesheet(self) -> Optional[Timesheet]:
    return (None
            if self.timesheetId is None else
            self.timesheetRepository.find(self.timesheetId))


  # checks
  def _checkTimesheet(self) -> bool:
    if self.timesheetId is None:
      self.send('Вы не подключены ни к какому расписанию', emoji='warning')
      return False
    if self.findTimesheet() is None:
      self.send('Расписание не найдено :( возможно, его удалили', emoji='fail')
      return False
    return True
  
  def _checkChannel(self) -> bool:
    if self.channel is None:
      self.send('Ошибкочка: канал не установлен, используйте /set_channel, '
                'чтобы установить канал', emoji='warning')
      return False
    return True

  # accessory
  def _eventIdFoundValidator(self, o: ValidatorObject):
    events = list(self.findTimesheet().events(predicat=lambda e: e.id == o.data))
    if len(events) == 0:
      o.success, o.error, o.emoji = (
        False,
        'Мероприятия с таким id не найдено. '
        + 'Используйте /show_events, чтобы посмотреть события',
        'warning'
      )
    return o
      
  def _sendPostFail(self, e = None):
    self.send(f'Произошла ошибка при попытке сделать пост :(\n\n'
              f'Возможные причины таковы:\n'
              f'1) Не верно указано название канала (сейчас: {self.channel})\n'
              f'2) Бот не является администратором канала' +
              ('' if e is None else
              f'\n\nВот как выглядит сообщение об ошибки: {e}'),
              emoji='warning')
    
  def _makePost(self, predicat = lambda _: True) -> [Piece]:
    timesheet = self.findTimesheet()
    events = list(timesheet.events(predicat=predicat))
    if len(events) == 0:
      self.send('Нельзя запостить пустое расписание', emoji='warning')
      return None
    return self.msgMaker.timesheetPost(events,
                                       head=timesheet.head,
                                       tail=timesheet.tail)

