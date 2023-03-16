from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import CallbackQuery
from typing import Optional, Any

from src.domain.locator import LocatorStorage, Locator
from src.entities.destination.destination import Destination
from src.entities.destination.settings import DestinationSettings
from src.entities.event.event import Place, Event
from src.entities.event.event_fields_parser import datetime_today
from src.entities.event.event_repository import EventRepo
from src.entities.event.event_tg_maker import TgEventInputFieldsConstructor
from src.entities.message_maker.accessory import send_message
from src.entities.message_maker.emoji import Emoji, get_emoji
from src.entities.message_maker.message_maker import MessageMaker
from src.entities.timesheet.timesheet import Timesheet
from src.entities.timesheet.timesheet_repository import TimesheetRepo

from src.entities.translation.translation import Translation
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
    chat: int = None,
    timesheet_id: int = None,
    destination: Destination = None,
    serialized: {str : Any} = None,
  ):
    Notifier.__init__(self)
    TgState.__init__(self)
    LocatorStorage.__init__(self, locator)
    self.tg: TeleBot = self.locator.tg()
    self.msgMaker: MessageMaker = self.locator.messageMaker()
    self.destinationRepo = self.locator.destinationRepo()
    self.eventRepo: EventRepo = self.locator.eventRepo()
    self.timesheetRepo: TimesheetRepo = self.locator.timesheetRepo()
    self.translationRepo: TranslationRepo = self.locator.translationRepo()
    self.logger: FLogger = self.locator.flogger()
    self.tgState = None
    if serialized is not None:
      self.deserialize(serialized)
    else:
      assert(chat is not None)
      self.chat = chat
      self.timesheetId = timesheet_id
      self.destination = destination
    self.eventPredicat = default_event_predicat

    
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
      'chat': self.chat,
      'timesheet_id': self.timesheetId,
      'destination_chat': self.destination.chat if self.destination is not None else None,
    }
    
  def deserialize(self, serialized: {str: Any}):
    self.chat = serialized['chat']
    self.timesheetId = serialized.get('timesheet_id')
    self.destination = None
    destination_chat = serialized.get('destination_chat')
    if destination_chat is not None:
      self.destination = self.destinationRepo.find(destination_chat)


  # HANDLERS FOR TELEGRAM
  # common commands
  def handleStart(self):
    self.terminateSubstate()
    self.send('Приветствуют тебя, мастер, заведующий расписанием!')

  def handleHelp(self):
    self.terminateSubstate()
    self.send(message=self.msgMaker.help())

  def handleShowTimesheetSettings(self):
    self.send(self.msgMaker.timesheet(self.findTimesheet()))

  def handleShowDestinationSettings(self):
    self.send(self.msgMaker.destination(self.destination))
    

  # event commands
  def handleMakeEvent(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    
    def on_form_entered(data: []):
      event = self.eventRepo.putWithId(lambda id: Event(
        id=id,
        desc=data[0],
        start=data[1],
        finish=None,
        place=Place(data[2]),
        url=data[3],
      ))
      timesheet = self.findTimesheet()
      if timesheet is None:
        self.send(f'Пока вы создавали мероприятие, расписание куда-то делось :(',
                  emoji='fail')
      else:
        timesheet.addEvent(event.id)
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
    def on_field_entered(event):
      state = None
      
      def on_event_field_entered(value, field_name: str):
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
      greeting='Введите ID мероприятия или слова, содержащиеся в названии',
      terminate_message='Прервано редактирование мероприятия',
      on_field_entered=on_field_entered,
      validator=self._eventValidator(),
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
      self.findTimesheet().removeEvent(id=data.id)
      self.eventRepo.remove(data.id)
      self.send('Мероприятие успешно удалено', emoji='ok')
      self.resetTgState()

    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите ID мероприятия или слова, содержащиеся в названии',
      terminate_message='Прервано удаление мероприятия',
      on_field_entered=on_field_entered,
      validator=self._eventValidator(),
    ))


  # timesheet commands
  def handleMakeTimesheet(self):
    def name_validator(o: ValidatorObject):
      timesheet = self.timesheetRepo.findByName(o.data)
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
      timesheet = self.timesheetRepo.putWithId(lambda id: Timesheet(
        locator=self.locator,
        id=id,
        name=name,
        password=pswd,
      ))
      self.timesheetId = timesheet.id
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
      timesheet = self.timesheetRepo.findByName(o.data)
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
      timesheet = self.timesheetRepo.findByName(tm['name'])
      if timesheet.password != o.data:
        o.success = False
        o.error = 'Пароль не подходит'
        o.emoji = 'fail'
      return o
    
    def on_form_entered(data: []):
      timesheet = self.timesheetRepo.findByName(data[0])
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
    names = [tm.name for tm in self.timesheetRepo.findAll(lambda _: True)]
    if len(names) == 0:
      self.send('Не найдено ни одного расписания :(', emoji='fail')
    else:
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


  # destination commands
  def handleSetDestination(self):
    def on_field_entered(data: str):
      self.destination = self.destinationRepo.find(data)
      self.send(f'Успешное подключение к {data}', emoji='ok')
      self.resetTgState()
      self.notify()

    self.terminateSubstate()
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите ссылку на публичный канал или группу',
      validator=TgPublicGroupOrChannelValidator(),
      terminate_message='Подключение прервано',
      on_field_entered=on_field_entered,
    ))

  def handleSetDestinationHead(self):
    self.terminateSubstate()
    if not self._checkDestination():
      return
  
    def on_entered(data):
      self.destination.sets.head = data
      self.destination.sets.notify()
      self.send('Заголовок успешно установлен!', emoji='ok')
      self.resetTgState()
  
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите заголовок для подключения',
      on_field_entered=on_entered,
      validator=PieceValidator(),
      terminate_message='Ввод заголовка прерван',
    ))

  def handleSetDestinationTail(self):
    self.terminateSubstate()
    if not self._checkDestination():
      return
  
    def on_entered(data):
      self.destination.sets.tail = data
      self.destination.sets.notify()
      self.send('Подвал успешно установлен!', emoji='ok')
      self.resetTgState()
  
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите подвал для подключения',
      on_field_entered=on_entered,
      validator=PieceValidator(),
      terminate_message='Ввод подвала прерван',
    ))
  
  def handlePost(self):
    self.terminateSubstate()
    if not self._checkTimesheet() or not self._checkDestination():
      return
    message = self._makePost(self.eventPredicat)
    if message is not None:
      self.post(message)
    
  def handlePostPreview(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    message = self._makePost(self.eventPredicat)
    if message is not None:
      self.send(message)


  # translate commands
  def handleTranslate(self):
    self.terminateSubstate()
    if not self._checkTimesheet() or not self._checkDestination():
      return
    
    tr = self.translationRepo.putWithId(lambda id: Translation(
      locator=self.locator,
      id=id,
      destination=self.destination,
      timesheet_id=self.timesheetId,
      creator=self.chat,
    ))
    if tr is not None:
      self.send('Успешно добавили трансляцию', emoji='ok')
    else:
      self._sendPostFail()
    return
    
  def handleTranslateToMessage(self):
    def on_field_entered(data):
      tr = self.translationRepo.putWithId(lambda id: Translation(
        locator=self.locator,
        id=id,
        destination=self.destinationRepo.find(data[0]),
        timesheet_id=self.timesheetId,
        message_id=data[1],
        creator=self.chat,
      ))
      if tr is not None and tr.updatePost():
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
    if not self._checkDestination():
      return
    self.translationRepo.removeAll(
      lambda tr: tr.destination.chat == self.destination.chat
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
        chat_id=self.destination.chat,
        text=message,
        disable_web_page_preview=True,
      )
      self.send('Пост успешно сделан!', emoji='ok')
    except ApiTelegramException as e:
      self._sendPostFail(e)

  def findTimesheet(self) -> Optional[Timesheet]:
    return (None
            if self.timesheetId is None else
            self.timesheetRepo.find(self.timesheetId))


  # checks
  def _checkTimesheet(self) -> bool:
    if self.timesheetId is None:
      self.send('Вы не подключены ни к какому расписанию', emoji='warning')
      return False
    if self.findTimesheet() is None:
      self.send('Расписание не найдено :( возможно, его удалили', emoji='fail')
      return False
    return True
  
  def _checkDestination(self) -> bool:
    if self.destination is None:
      self.send('Ошибкочка: канал не установлен, используйте /set_destination, '
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
    else:
      o.data = events[0]
    return o
  
  def _eventFoundByWordsValidator(self, o: ValidatorObject):
    words = o.data.split()
    
    def predicat(event):
      for word in words:
        if word.lower() not in event.desc.lower():
          return False
      return True
    
    events = list(self.findTimesheet().events(predicat=predicat))
    if len(events) == 0:
      o.success, o.error, o.emoji = (
        False,
        'Мероприятий, содержащих все эти слова, не найдено :(',
        'fail'
      )
    elif len(events) > 1:
      o.success, o.error, o.emoji = (
        False,
        'Мероприятий, содержащих все эти слова, найдено сразу несколько:\n\n'
        + '\n'.join([self.msgMaker.eventPreview(event) for event in events]),
        'warning'
      )
    else:
      o.data = events[0]
    return o
  
  def _eventValidator(self):
    def validate(o: ValidatorObject) -> ValidatorObject:
      obj = IntValidator().validate(o)
      if obj.success:
        return self._eventIdFoundValidator(obj)
      return ChainValidator([
        TextValidator(),
        FunctionValidator(self._eventFoundByWordsValidator),
      ]).validate(o)
    
    return FunctionValidator(validate)

  def _sendPostFail(self, e = None):
    self.send(f'Произошла ошибка при попытке сделать пост :(\n\n'
              f'Возможные причины таковы:\n'
              f'1) Не верно указано название канала (сейчас: {self.destination.chat})\n'
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
    return self.msgMaker.timesheetPost(
      events,
      DestinationSettings.merge(
        timesheet.destinationSets,
        DestinationSettings.default()
        if self.destination is None else
        self.destination.sets
      ),
    )
  

def default_event_predicat(event: Event) -> bool:
  return event.start >= datetime_today()