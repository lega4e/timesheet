import datetime as dt

from copy import deepcopy

from telebot import TeleBot
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, Any

from src.domain.locator import LocatorStorage, Locator
from src.domain.post_parser import parse_post
from src.domain.tg.tg_destination import TgDestination
from src.entities.action.action import Action, ActionTgAutoForward
from src.entities.commands_manager.commands import CommandDescription, global_command_list
from src.entities.destination.destination import Destination
from src.entities.destination.settings import DestinationSettings
from src.entities.event.event import Place, Event
from src.entities.event.event_fields_parser import datetime_today
from src.entities.event.event_repository import EventRepo
from src.entities.event.event_tg_maker import TgEventInputFieldsConstructor
from src.utils.tg.send_message import send_message
from src.utils.tg.tg_emoji import Emoji, get_emoji
from src.entities.message_maker.message_maker import MessageMaker
from src.entities.timesheet.timesheet import Timesheet
from src.entities.timesheet.timesheet_repository import TimesheetRepo

from src.entities.translation.translation import Translation
from src.entities.translation.translation_repository import TranslationRepo
from src.utils.logger.logger import FLogger
from src.utils.notifier import Notifier
from src.utils.repeater import Period
from src.utils.serialize import Serializable
from src.utils.tg.tg_input_field import TgInputField, InputFieldButton
from src.utils.tg.tg_input_form import TgInputForm
from src.utils.tg.tg_state import TgState
from src.utils.tg.tg_state_branch import TgStateBranch, BranchButton
from src.utils.tg.utils import list_to_layout
from src.utils.tg.value_validators import *
from src.utils.utils import insert_between, reduce_list

import src.entities.message_maker.piece

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
    self.actionRepo = self.locator.actionRepo()
    self.tgState = None
    self.sourceMessage = None
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
    self.send('Непонятно.. что ты хочешь..? напиши /commands или /help',
              emoji='fail')
    
  def _handleMessageBefore(self, m: Message) -> bool:
    if m.forward_from_chat is not None or m.forward_from is not None:
      self.handleForward(m)
      return True
    if m.text is not None and m.text[0] == '/':
      self.terminateSubstate()
      self.send('Неизвестная команда.. попробуй /commands', emoji='fail')
      return True
    return False

  def _handleCallbackQuery(self, q: CallbackQuery):
    coms = [c for c in global_command_list if q.data == c.preview]
    if len(coms) > 0:
      self.handle(coms[0])
      self.tg.answer_callback_query(q.id, text=coms[0].short)
    else:
      self.tg.answer_callback_query(q.id, text='Непонятно..')

  def serialize(self) -> {str : Any}:
    return {
      'chat': self.chat,
      'timesheet_id': self.timesheetId,
      'destination_id': self.destination.id if self.destination is not None else None,
    }
    
  def deserialize(self, serialized: {str: Any}):
    self.chat = serialized['chat']
    self.timesheetId = serialized.get('timesheet_id')
    self.destination = self.destinationRepo.find(serialized.get('destination_id'))


  # HANDLERS FOR TELEGRAM
  def handle(self, command: CommandDescription):
    self.locator.flogger().info(f'handle {command.preview}')
    exec(f'self.{command.userCommand}()')
  
  def handleForward(self, m: Message):
    answer = parse_post(m)
    if answer.datetime is None and answer.url is None and answer.name is None:
      self.send('Ни одно поле не получилось извлечь :( какой-то дурацкий пост', emoji='fail')
      return
    fields = [field for field in [
      ('название', answer.name),
      ('ссылка', answer.url),
      ('дата и время', None if answer.datetime is None else answer.datetime.strftime('%x %R')),
    ] if field[1] is not None]
    self.send(P('Из форварда успешно получены поля:\n') + reduce_list(
      lambda a, b: a + b,
      insert_between(
        [P(f'{Emoji.STRAWBERRY} {title} (') + P(f'{value}', types=['code']) + P(')')
         for title, value in fields],
        P('\n')
      ),
      P(),
    ))
    self.send('Вы сможете подредактировать их после окончательного создания мероприятия, '
              'а сейчас введите остальные поля', emoji='edit')

    def on_form_entered(data):
      counter = 0
      if answer.name is None:
        answer.name = data[counter]
        counter += 1
      if answer.datetime is None:
        answer.datetime = data[counter]
        counter += 1
      answer.place = Place(data[counter], data[counter+1])
      counter += 2
      if answer.url is None:
        answer.url = data[counter]
        counter += 1
        
      event = Event(
        id=self.eventRepo.newId(),
        desc=answer.name,
        start=answer.datetime,
        finish=None,
        place=answer.place,
        url=answer.url,
        creator=self._getCreator(),
      )
      self.eventRepo.put(event)
      self.findTimesheet().addEvent(event.id)
      self.send(P('Мероприятие успешно добавлено! Проверьте все поля', emoji='ok'))
      self.resetTgState()
      self._editEvent(event)

    self.terminateSubstate()
    if not self._checkTimesheet():
      return

    constructor = TgEventInputFieldsConstructor(tg=self.tg, chat=self.chat)
    self.setTgState(TgInputForm(
      tg=self.tg,
      chat=self.chat,
      terminate_message='Создание мероприятия преравно',
      on_form_entered=on_form_entered,
      fields=[field for field in [
        constructor.makeNameInputField(lambda _: True)
          if answer.name is None else None,
        constructor.makeDatetimeInputField(lambda _: True)
          if answer.datetime is None else None,
        constructor.makePlaceInputField(lambda _: True, self.findTimesheet().places),
        constructor.makeOrgInputField(lambda _: True, self.findTimesheet().orgs),
        constructor.makeUrlInputField(lambda _: True)
          if answer.url is None else None]
      if field is not None]
    ))

  def handleStart(self):
    self.terminateSubstate()
    self.send('Приветствуют тебя! Для начала тебе нужно подключиться'
              'к расписанию (/set_timesheet) или создать своё (/make_timesheet).'
              'Чтобы увидеть меню команд введи /commands. И помню: расписатель'
              'живёт в каждом из нас ;)')

  def handleHelp(self):
    self.terminateSubstate()
    self.send(message=self.msgMaker.help())

  def handleCommands(self):
    self._handleCommandPage([['/events', '/destination'],
                             ['/timesheet', '/help']])

  def handleEvents(self):
    self._handleCommandPage([
      ['/make_event', '/replay'],
      ['/remove_event', '/edit_event'],
      ['/show_events'],
    ])

  def handleDestination(self):
    self._handleCommandPage([
      ['/show_destination', '/set_destination'],
      ['/show_destination_info', '/autoposts'],
      ['/translate'],
      ['/translate_to_message'],
    ])

  def handleAutoposts(self):
    self._handleCommandPage([
      ['/show_autoposts'],
      ['/make_autopost', '/remove_autopost'],
    ])

  def handleTimesheet(self):
    self._handleCommandPage([
      ['/make_timesheet', '/set_timesheet'],
      ['/show_timesheet_info', '/translations'],
      ['/places_and_orgs'],
    ])
    
  def handlePlacesAndOrgs(self):
    self._handleCommandPage([
      ['/show_places', '/set_places'],
      ['/show_orgs', '/set_orgs'],
    ])

  def handleTranslations(self):
    self._handleCommandPage([
      ['/show_translations'],
      ['/remove_translation'],
      ['/clear_translations'],
    ])

  # event commands
  def handleMakeEvent(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    
    def on_form_entered(data: []):
      event = self.eventRepo.put(Event(
        id=self.eventRepo.newId(),
        desc=data[0],
        start=data[1],
        finish=None,
        place=Place(name=data[2], org=data[3]),
        url=data[4],
        creator=self._getCreator(),
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
      fields=[constructor.makeNameInputField(lambda _: True),
              constructor.makeDatetimeInputField(lambda _: True),
              constructor.makePlaceInputField(lambda _: True,
                                              self.findTimesheet().places),
              constructor.makeOrgInputField(lambda _: True,
                                            self.findTimesheet().orgs),
              constructor.makeUrlInputField(lambda _: True)]
    ))
    
  def handleReplay(self):
    def on_field_entered(data):
      start = deepcopy(data.start)
      while True:
        start += dt.timedelta(weeks=1)
        if start >= datetime_today():
          break
      event = self.eventRepo.put(Event(
        id=self.eventRepo.newId(),
        desc=data.desc,
        start=start,
        finish=None,
        place=deepcopy(data.place),
        url=None,
        creator=data.creator,
      ))
      self.findTimesheet().addEvent(event.id)
      self.send(P('Мероприятие успешно добавлено! Проверьте все поля (',emoji='ok') +
                P('и добавьте URL!', types=['underline', 'bold']) + P(')'))
      self.resetTgState()
      self._editEvent(event)
      
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите ID мероприятия или слова, содержащиеся в названии',
      terminate_message='Прерван повтор мероприятия',
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

  def handleEditEvent(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите ID мероприятия или слова, содержащиеся в названии',
      terminate_message='Прервано редактирование мероприятия',
      on_field_entered=self._editEvent,
      validator=self._eventValidator(),
    ))

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

  # places and organizators
  def handleSetPlaces(self):
    def on_place_enter(data: str):
      timesheet = self.findTimesheet()
      timesheet.places = [line.strip() for line in data.split('\n')]
      self.send(f'Места  успешно установлены', emoji='ok')
      timesheet.notify(timesheet.EMIT_PLACES_CHANGED)
      self.resetTgState()
  
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите места (одна строка — одно место). '
               'Все старые места будут удалены и заменены новыми.\n\n'
               'Посмотреть существующие места: /show_places',
      terminate_message='Установка мест прервана',
      validator=TextValidator(),
      on_field_entered=on_place_enter,
      buttons=[[InputFieldButton('Очистить', [], 'Очищено')]],
    ))

  def handleShowPlaces(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    timesheet = self.findTimesheet()
    if len(timesheet.places) == 0:
      self.send('А никого :(', emoji='fail')
    else:
      self.send(P('Существующие места:\n') +
                P('\n'.join(timesheet.places), types='code') +
                '\n\nУстановить места: /set_places')

  def handleSetOrgs(self):
    def on_orgs_enter(data: str):
      timesheet = self.findTimesheet()
      timesheet.orgs = [line.strip() for line in data.split('\n')]
      self.send(f'Организаторы успешно установлены', emoji='ok')
      timesheet.notify(timesheet.EMIT_ORGS_CHANGED)
      self.resetTgState()
  
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите организаторов (одна строка — один организатор). '
               'Все старые организаторы будут удалены и заменены новыми.\n\n'
               'Посмотреть существующие организаторы: /show_orgs',
      terminate_message='Установка организаторов прервана',
      validator=TextValidator(),
      on_field_entered=on_orgs_enter,
      buttons=[[InputFieldButton('Очистить', [], 'Очищено')]],
    ))

  def handleShowOrgs(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    timesheet = self.findTimesheet()
    if len(timesheet.orgs) == 0:
      self.send('А никого :(', emoji='fail')
    else:
      self.send(P('Существующие организаторы:\n') +
                P('\n'.join(timesheet.orgs), types='code') +
                '\n\nУстановить организаторов: /set_places')


  # timesheet commands
  def handleMakeTimesheet(self):
    def name_validator(o: ValidatorObject):
      timesheet = self.timesheetRepo.findByName(o.data)
      if timesheet is not None:
        o.success = False
        o.error = (P('Расписание с именем ', emoji='fail') +
                   P(f'{o.data}', types='code') +
                   ' уже есть :( давай по новой')
      return o
    
    def on_form_entered(data: []):
      name = data[0]
      pswd = data[1]
      timesheet = self.timesheetRepo.put(Timesheet(
        locator=self.locator,
        id=self.timesheetRepo.newId(),
        name=name,
        password=pswd,
      ))
      self.timesheetId = timesheet.id
      self.send(P('Расписание ', emoji='ok') +
                P(f'{name}', types='code') +
                P(' с паролем ') +
                P(f'{pswd}', types='code') +
                P(' успешно создано'))
      self.resetTgState()
      self.notify()
    
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
          validator=IdValidator(error=IdValidator.PSWD_ERROR_MESSAGE,
                                is_password=True),
          on_field_entered=lambda _: None,
        )
      ]
    ))

  def handleShowTimesheetInfo(self):
    self.terminateSubstate()
    self.send(
      self.msgMaker.timesheet(self.findTimesheet()),
      reply_markup=coms2markup([
        ['/set_timesheet'],
        ['/set_timesheet_head', '/set_timesheet_tail'],
        ['/set_timesheet_event_format']
      ]),
    )

  def handleSetTimesheet(self):
    tm = {}
    
    def name_validator(o: ValidatorObject):
      timesheet = self.timesheetRepo.findByName(o.data)
      if timesheet is None:
        o.success = False
        o.error = (P('Расписание с названием ', emoji='fail') +
                   P(f'{o.data}', types='code') +
                   P(' не найдено :( Существующие расписания ') +
                   P('можно посмотреть командой /show_timesheet_list'))
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
        o.error = P('Пароль не подходит', emoji='fail')
      return o
    
    def on_form_entered(data: []):
      timesheet = self.timesheetRepo.findByName(data[0])
      self.timesheetId = timesheet.id
      self.send(P('Успешно выбрано расписание ', emoji='ok') +
                P(f'{data[0]}', types='code'))
      self.resetTgState()
      self.notify()

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
      timehseet = self.findTimesheet()
      timehseet.destinationSets.head = data
      timehseet.destinationSets.notify()
      self.send('Заголовок успешно установлен!', emoji='ok')
      self.resetTgState()
      
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите заголовок расписания',
      on_field_entered=on_entered,
      validator=PieceValidator(),
      terminate_message='Ввод заголовка прерван',
      buttons=[[InputFieldButton('Очистить', None, 'Очищено')]],
    ))

  def handleSetTimesheetTail(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
  
    def on_entered(data):
      if not self._checkTimesheet():
        return
      timehseet = self.findTimesheet()
      timehseet.destinationSets.tail = data
      timehseet.destinationSets.notify()
      self.send('Подвал успешно установлен!', emoji='ok')
      self.resetTgState()
  
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите подвал расписания',
      on_field_entered=on_entered,
      validator=PieceValidator(),
      terminate_message='Ввод подвала прерван',
      buttons=[[InputFieldButton('Очистить', None, 'Очищено')]],
    ))

  def handleSetTimesheetEventFormat(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return

    timesheet = self.findTimesheet()
    def on_entered(data):
      if not self._checkTimesheet():
        return
      timesheet.destinationSets.lineFormat = data
      timesheet.destinationSets.notify()
      self.send('Формат успешно установлен!', emoji='ok')
      self.resetTgState()
  
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting=self.msgMaker.eventFormatInput(timesheet.destinationSets),
      on_field_entered=on_entered,
      validator=TextValidator(),
      terminate_message='Ввод формата прерван',
      buttons=[[InputFieldButton('Очистить', None, 'Очищено')]],
    ))

  def handleShowTimesheetList(self):
    self.terminateSubstate()
    names = [tm.name for tm in self.timesheetRepo.findAll(lambda _: True)]
    if len(names) == 0:
      self.send('Не найдено ни одного расписания :(', emoji='fail')
    else:
      self.send(
        P('Существующие расписания:\n') +
        reduce_list(
          lambda a, b: a + b,
          insert_between(
            [P(f'{Emoji.TIMESHEET_ITEM} ') + P(f'{name}', types='code')
             for name in names],
            '\n',
          ),
          P(),
        )
      )


  # destination commands
  def handleSetDestination(self):
    def on_field_entered(data: str):
      self.destination = self.destinationRepo.findByChatId(data)
      self.send(f'Успешное подключение к {data}', emoji='ok')
      self.resetTgState()
      self.notify()

    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите ссылку на публичный канал или группу',
      validator=TgPublicGroupOrChannelValidator(),
      terminate_message='Установка канала прервана',
      on_field_entered=on_field_entered,
    ))
    
  def handleShowDestination(self):
    self.resetTgState()
    if self.destination is not None:
      self.send(self.destination.chat.getUrl(), emoji=Emoji.POINT_RIGHT)
    else:
      self.send('А такого нет', emoji='fail')

  def handleShowDestinationInfo(self):
    self.terminateSubstate()
    self.send(
      self.msgMaker.destination(self.destination),
      reply_markup=coms2markup([
          ['/set_destination'],
          ['/set_destination_head', '/set_destination_tail'],
          ['/set_destination_black_list', '/set_destination_words_black_list'],
          ['/set_destination_event_format']
      ])
    )
    
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
      buttons=[[InputFieldButton('Очистить', None, 'Очищено')]],
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
      buttons=[[InputFieldButton('Очистить', None, 'Очищено')]],
    ))

  def handleSetDestinationEventFormat(self):
    self.terminateSubstate()
    if not self._checkDestination():
      return
  
    def on_entered(data):
      if not self._checkDestination():
        return
      self.destination.sets.lineFormat = data
      self.destination.sets.notify()
      self.send('Формат успешно установлен!', emoji='ok')
      self.resetTgState()
  
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting=self.msgMaker.eventFormatInput(self.destination.sets),
      on_field_entered=on_entered,
      validator=TextValidator(),
      terminate_message='Ввод формата прерван',
      buttons=[[InputFieldButton('Очистить', None, 'Очищено')]],
    ))

  def handleSetDestinationBlackList(self):
    self.terminateSubstate()
    if not self._checkDestination():
      return
  
    def on_entered(data):
      self.destination.sets.blackList = set(data)
      self.destination.sets.notify()
      self.send('События с этими идентификаторами больше не будут показываться! '
                'Посмотреть все настройки: /show_destination_settings',
                emoji='ok')
      self.resetTgState()
  
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите список идентификаторов событий, '
               'которые вы хотите внести в чёрный список',
      on_field_entered=on_entered,
      validator=ChainValidator([TextValidator(), IntegerListValidator()]),
      terminate_message='Ввод прерван',
      buttons=[[InputFieldButton('Оставить пустым', set(), 'Пусть будет пусто')]],
    ))

  def handleSetDestinationWordsBlackList(self):
    self.terminateSubstate()
    if not self._checkDestination():
      return
  
    def on_entered(data):
      self.destination.sets.wordsBlackList = data
      self.destination.sets.notify()
      self.send('События, содержащие эти слова, не будут показываться! '
                'Посмотреть все настройки: /show_destination_settings',
                emoji='ok')
      self.resetTgState()
  
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите список идентификаторов событий, '
               'которые вы хотите внести в чёрный список',
      on_field_entered=on_entered,
      validator=ChainValidator([TextValidator(), WordListValidator()]),
      terminate_message='Ввод прерван',
      buttons=[[InputFieldButton('Оставить пустым', [], 'Пусть будет пусто')]],
    ))
  

  # translate commands
  def handlePostPreview(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    message = self._makePost(self.eventPredicat)
    if message is not None:
      self.send(message)

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
      self.send(P('Успешно добавили ', emoji='ok') +
                P('трансляцию', url=self.destination.getUrl(tr.messageId)))
    else:
      self._sendPostFail()
    return
    
  def handleTranslateToMessage(self):
    def on_field_entered(data):
      tr = self.translationRepo.putWithId(lambda id: Translation(
        locator=self.locator,
        id=id,
        destination=self.destinationRepo.findByChatId(data[0]),
        timesheet_id=self.timesheetId,
        message_id=data[1],
        creator=self.chat,
      ))
      if tr is not None and tr.updatePost():
        self.send(P('Успешно добавили ', emoji='ok') +
                  P('трансляцию в сообщение',
                         url=tr.destination.getUrl(tr.messageId)))
      else:
        self.send(P('Что-то пошло не так..', emoji='fail'))
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
    
  def handleShowTranslations(self):
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    timesheet_id = self.findTimesheet().id
    trs = self.translationRepo.findAll(lambda tr: tr.timesheetId == timesheet_id)
    if len(trs) == 0:
      self.send('А никого :(', emoji='fail')
    else:
      self.send('Вот они все:\n' + '\n'.join(sorted(
        f'{get_emoji("translation")} {tr.destination.getUrl(tr.messageId)}' for tr in trs
      )))
      
  def handleRemoveTranslation(self):
    def on_field_entered(data):
      tr = self.translationRepo.findIf(
        lambda t: (t.timesheetId == self.timesheetId and
                   t.destination.chat.chatId == data[0] and
                   t.messageId == data[1])
      )
      if tr is None:
        self.send('Не найдено трансляции в данное сообщение :(', emoji='fail')
      else:
        tr.emitDestroy('remove by command')
        self.send('Трансляция успешно удалена!', emoji='ok')
      self.resetTgState()
  
    self.terminateSubstate()
    if not self._checkTimesheet():
      return
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите ссылку на пост',
      validator=TgMessageUrlValidator(),
      terminate_message='Удаление трансляции прервано',
      on_field_entered=on_field_entered,
    ))
    
  def handleClearTranslations(self):
    self.terminateSubstate()
    if not self._checkDestination():
      return
    self.translationRepo.removeAll(
      lambda tr: tr.destination.chat.chatId == self.destination.chat.chatId
    )
    self.send('Успешно удалили все трансляции для выбранного канала', emoji='ok')


  # auto post commands
  def handleMakeAutopost(self):
    self.terminateSubstate()
    if not self._checkTimesheet() or not self._checkDestination():
      return
  
    def on_form_entered(data):
      self.actionRepo.put(ActionTgAutoForward(
        id=self.actionRepo.newId(),
        period=Period(point=correct_datetime(data[0]), delta=data[1]),
        chat=self.destination.chat,
        timesheet_id=self.timesheetId,
        creator=self.chat,
      ))
      self.send('Автопост успешно добавлен!', emoji='ok')
      self.resetTgState()
  
    self.setTgState(TgInputForm(
      tg=self.tg,
      chat=self.chat,
      terminate_message='Создание автопоста прервано',
      on_form_entered=on_form_entered,
      fields=[
        TgInputField(
          tg=self.tg,
          chat=self.chat,
          greeting='Введите дату и время, с которой начать автопост',
          on_field_entered=lambda _: True,
          validator=DatetimeValidator(),
        ),
        TgInputField(
          tg=self.tg,
          chat=self.chat,
          greeting='Выберете или введите в часах период, с котроым делать автопост',
          on_field_entered=lambda _: True,
          validator=ChainValidator([
            IntValidator(),
            FunctionValidator(lambda o: dt.timedelta(hours=o.data)),
          ]),
          buttons=[[InputFieldButton('Каждый день', dt.timedelta(days=1)),
                    InputFieldButton('Каждую неделю', dt.timedelta(weeks=1))],
                   [InputFieldButton('Каждую вторую неделю', dt.timedelta(weeks=2))]],
        ),
      ]
    ))

  def handleShowAutoposts(self):
    autoposts = self.actionRepo.findAll(lambda a: a.type == Action.TG_AUTO_FORWARD)
    if len(autoposts) == 0:
      self.send('А никого :(', emoji='fail')
      return
    self.send('Список автопостов:'
              '\n'.join([f'{Emoji.POINT_RIGHT} #{autopost.id} {autopost.chat.chatId} '
                         f'{autopost.period.point.strftime("%x %R")} every '
                         f'{int(autopost.period.delta.total_seconds() / 3600 * 1000) / 1000} hours'
                         for autopost in autoposts]))
    
  def handleRemoveAutopost(self):
    self.terminateSubstate()
  
    def on_field_entered(data):
      self.actionRepo.remove(key=data.id)
      self.send('Автопост успешно удалён', emoji='ok')
      self.resetTgState()
  
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting='Введите ID автопоста',
      terminate_message='Прервано удаление мероприятия',
      on_field_entered=on_field_entered,
      validator=self._autopostValidator(),
    ))

  # OTHER
  def send(self, message, emoji: str = None, reply_markup = None):
    if isinstance(message, str):
      message = P(message, emoji=emoji)
    send_message(
      tg=self.tg,
      chat=self.chat,
      text=message,
      disable_web_page_preview=True,
      reply_markup=reply_markup,
    )
    
  def findTimesheet(self) -> Optional[Timesheet]:
    return (None
            if self.timesheetId is None else
            self.timesheetRepo.find(self.timesheetId))

  def _handleCommandPage(self, coms):
    def on_field_entered(command: CommandDescription):
      self.handle(command)
      self.resetTgState()
  
    coms = [[com(c) for c in row] for row in coms]
    pieces = self.msgMaker.pageWithCommands(
      reduce_list(lambda a, b: a + b, coms, [])
    )
    self.setTgState(TgInputField(
      tg=self.tg,
      chat=self.chat,
      greeting=pieces,
      greeting_emoji=None,
      validator=FalseValidator(),
      on_field_entered=on_field_entered,
      buttons=[[com2button(c) for c in row] for row in coms],
    ))

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
  
  def _autopostValidator(self):
    def find_autopost_validator(o: ValidatorObject) -> ValidatorObject:
      autopost = self.actionRepo.find(o.data)
      if autopost is None:
        o.success = False
        o.error = P('Не получилось найти автопост с таким ID.'
                    'См. /show_autoposts', emoji='fail')
      else:
        o.data = autopost
      return o
    
    return ChainValidator([IntValidator(), FunctionValidator(find_autopost_validator)])

  def _sendPostFail(self, e = None):
    self.send(f'Произошла ошибка при попытке сделать пост :(\n\n'
              f'Возможные причины таковы:\n'
              f'1) Не верно указано название канала (сейчас: {self.destination.chat})\n'
              f'2) Бот не является администратором канала' +
              ('' if e is None else
              f'\n\nВот как выглядит сообщение об ошибки: {e}'),
              emoji='warning')
    
  def _makePost(self, predicat = lambda _: True) -> Optional[Pieces]:
    timesheet = self.findTimesheet()
    events = list(timesheet.events(predicat=predicat))
    if len(events) == 0:
      self.send('Расписание пустое :(', emoji='fail')
      return None
    return self.msgMaker.timesheetPost(
      events,
      DestinationSettings.merge(
        timesheet.destinationSets,
        DestinationSettings()
        if self.destination is None else
        self.destination.sets
      ),
    )
  
  def _getCreator(self):
    return ((self.sourceMessage.chat.username
               if self.sourceMessage.chat.username[0] == '@' else
               '@' + self.sourceMessage.chat.username)
            if self.sourceMessage is not None else None)

  def _editEvent(self, event: Event):
    state = None

    def on_event_field_entered(value, field_name: str):
      if field_name == 'name':
        event.desc = value
      elif field_name == 'start':
        event.start = value
      elif field_name == 'place':
        event.place.name = value
      elif field_name == 'org':
        event.place.org = value
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
      chat=TgDestination(chat_id=self.chat),
      make_buttons=lambda: [
        [BranchButton(
          'Название',
          constructor.makeNameInputField(
            lambda value: on_event_field_entered(value, 'name')
          ),
        ),
          BranchButton(
            'Начало',
            constructor.makeDatetimeInputField(
              lambda value: on_event_field_entered(value, 'start')
            ),
          ),
          BranchButton(
            'Ссыль',
            constructor.makeUrlInputField(
              lambda value: on_event_field_entered(value, 'url')
            ),
          )],
        [BranchButton(
          'Место',
          constructor.makePlaceInputField(
            lambda value: on_event_field_entered(value, 'place'),
            places=self.findTimesheet().places,
          )
        ),
          BranchButton(
            'Организатор',
            constructor.makeOrgInputField(
              lambda value: on_event_field_entered(value, 'org'),
              orgs=self.findTimesheet().orgs,
            )
          )],
        [BranchButton('Завершить', action=complete, callback_answer='Завершено')],
      ],
      make_message=lambda: P(f'Название:    {event.desc}\n' +
                             f'Начало:      {event.start.strftime("%x %X")}\n' +
                             f'Место:       {event.place.name}\n' +
                             (f'Организатор: {event.place.org}\n'
                              if event.place.org is not None else '') +
                             f'URL:         {event.url}',
                             types='code'),
      on_terminate=lambda: self.send('Редактирование мероприятия заверщено', emoji='ok')
    )
    self.setTgState(state, terminate=False)


def default_event_predicat(event: Event) -> bool:
  return event.start >= datetime_today()

def com(preview: str) -> CommandDescription:
  return [c for c in global_command_list if c.preview == preview][0]

def com2button(command: CommandDescription) -> InputFieldButton:
  return InputFieldButton(
    title=command.short,
    data=command,
    answer=command.short,
    qb=command.preview,
  )

def coms2markup(commands: List[List[str]]) -> InlineKeyboardMarkup:
  markup = InlineKeyboardMarkup()
  commands = [[com(c) for c in row] for row in commands]
  for row in commands:
    markup.add(*[
      InlineKeyboardButton(text=c.short, callback_data=c.preview)
      for c in row
    ])
  return markup
    