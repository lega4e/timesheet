from telebot.callback_data import CallbackData
from telebot.types import BotCommand, CallbackQuery

from src.domain.di import glob
from src.entities.message_maker.help import commands

di = glob()
tg = di.tg()
log = di.flogger()
users = di.userRepository()


def user_finder(func):
  def wrapper(m, res=False):
    func(users.find(m.chat.id), m, res)
  return wrapper


def log_text(func):
  def wrapper(m, res=False):
    log.text(m)
    func(m, res)
  return wrapper


# common commands
@tg.message_handler(commands=['start'])
@log_text
@user_finder
def handle_start(user, _, __=False):
  user.handleStart()


@tg.message_handler(commands=['help'])
@log_text
@user_finder
def handle_help(user, _, __=False):
  user.handleHelp()


# event commands
@tg.message_handler(commands=['make_event'])
@log_text
@user_finder
def handle_make_event(user, _, __=False):
  user.handleMakeEvent()


@tg.message_handler(commands=['show_events'])
@log_text
@user_finder
def handle_show_events(user, _, __=False):
  user.handleShowEvents()


@tg.message_handler(commands=['edit_event'])
@log_text
@user_finder
def handle_edit_event(user, m, __=False):
  user.handleEditEvent(m.text[len('edit_event')+1:].strip())


@tg.message_handler(commands=['remove_event'])
@log_text
@user_finder
def handle_remove_event(user, m, __=False):
  user.handleRemoveEvent(m.text[len('remove_event')+1:].strip())


# timesheet commands
@tg.message_handler(commands=['make_timesheet'])
@log_text
@user_finder
def handle_make_timesheet(user, m, __=False):
  user.handleMakeTimesheet(m.text[len('make_timesheet')+1:].strip())


@tg.message_handler(commands=['set_timesheet'])
@log_text
@user_finder
def handle_set_timesheet(user, m, __=False):
  user.handleSetTimesheet(m.text[len('set_timesheet')+1:].strip())
  
  
# post commands
@tg.message_handler(commands=['set_channel'])
@log_text
@user_finder
def handle_set_channel(user, m, __=False):
  user.handleSetChannel(m.text[len('set_channel')+1:].strip())


@tg.message_handler(commands=['post'])
@log_text
@user_finder
def handle_post(user, _, __=False):
  user.handlePost()


@tg.message_handler(commands=['post_preview'])
@log_text
@user_finder
def handle_post(user, _, __=False):
  user.handlePostPreview()


@tg.message_handler(commands=['translate'])
@log_text
@user_finder
def handle_translate(user, m, __=False):
  user.handleTranslate(m.text[len('translate')+1:].strip())


@tg.message_handler(commands=['clear_translations'])
@log_text
@user_finder
def handle_clear_translations(user, _, __=False):
  user.handleClearTranslations()
  

# other
@tg.message_handler(content_types=['text'])
@log_text
@user_finder
def handle_text(user, m, __=False):
  user.handleText(m.text)
  
  
@tg.callback_query_handler(func=lambda call: True)
def callback_query(call: CallbackQuery):
  user = users.find(call.from_user.id)
  user.callbackQuery(call)


def set_my_commands():
  tg.set_my_commands(commands=[
    BotCommand(command=com.name, description=com.short)
    for com in commands
  ])