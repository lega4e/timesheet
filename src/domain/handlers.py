from telebot.types import BotCommand, CallbackQuery, Message

from src.domain.locator import glob
from src.entities.message_maker.help import commands

locator = glob()
tg = locator.tg()
log = locator.flogger()
users = locator.userRepo()


def user_finder(func):
  def wrapper(m, res=False):
    func(users.find(m.chat.id) if m.chat.id > 0 else None, m, res)
  return wrapper


def log_text(func):
  def wrapper(m, res=False):
    if m.chat.id > 0:
      log.text(m)
    func(m, res)
  return wrapper


# common commands
@tg.message_handler(commands=['start'])
@log_text
@user_finder
def handle_start(user, _, __=False):
  if user is not None:
    user.handleStart()


@tg.message_handler(commands=['help'])
@log_text
@user_finder
def handle_help(user, _, __=False):
  if user is not None:
    user.handleHelp()


@tg.message_handler(commands=['show_timesheet_info'])
@log_text
@user_finder
def handle_show_timesheet_settings(user, _, __=False):
  if user is not None:
    user.handleShowTimesheetInfo()


@tg.message_handler(commands=['show_destination_info'])
@log_text
@user_finder
def handle_show_destination_settings(user, _, __=False):
  if user is not None:
    user.handleShowDestinationInfo()


# event commands
@tg.message_handler(commands=['make_event'])
@log_text
@user_finder
def handle_make_event(user, _, __=False):
  if user is not None:
    user.handleMakeEvent()


@tg.message_handler(commands=['show_events'])
@log_text
@user_finder
def handle_show_events(user, _, __=False):
  if user is not None:
    user.handleShowEvents()


@tg.message_handler(commands=['edit_event'])
@log_text
@user_finder
def handle_edit_event(user, _, __=False):
  if user is not None:
    user.handleEditEvent()


@tg.message_handler(commands=['remove_event'])
@log_text
@user_finder
def handle_remove_event(user, _, __=False):
  if user is not None:
    user.handleRemoveEvent()


@tg.message_handler(commands=['add_place'])
@log_text
@user_finder
def handle_add_place(user, _, __=False):
  if user is not None:
    user.handleAddPlace()


@tg.message_handler(commands=['show_places'])
@log_text
@user_finder
def handle_show_places(user, _, __=False):
  if user is not None:
    user.handleShowPlaces()


@tg.message_handler(commands=['remove_places'])
@log_text
@user_finder
def handle_remove_places(user, _, __=False):
  if user is not None:
    user.handleRemovePlaces()


# timesheet commands
@tg.message_handler(commands=['make_timesheet'])
@log_text
@user_finder
def handle_make_timesheet(user, _, __=False):
  if user is not None:
    user.handleMakeTimesheet()


@tg.message_handler(commands=['set_timesheet'])
@log_text
@user_finder
def handle_set_timesheet(user, _, __=False):
  if user is not None:
    user.handleSetTimesheet()
  
  
# destination commands
@tg.message_handler(commands=['set_destination'])
@log_text
@user_finder
def handle_set_destination(user, _, __=False):
  if user is not None:
    user.handleSetDestination()


@tg.message_handler(commands=['set_destination_head'])
@log_text
@user_finder
def handle_set_destination_head(user, _, __=False):
  if user is not None:
    user.handleSetDestinationHead()


@tg.message_handler(commands=['set_destination_tail'])
@log_text
@user_finder
def handle_set_destination_tail(user, _, __=False):
  if user is not None:
    user.handleSetDestinationTail()


@tg.message_handler(commands=['set_destination_black_list'])
@log_text
@user_finder
def handle_set_destination_black_list(user, _, __=False):
  if user is not None:
    user.handleSetDestinationBlackList()


@tg.message_handler(commands=['set_destination_words_black_list'])
@log_text
@user_finder
def handle_set_destination_word_black_list(user, _, __=False):
  if user is not None:
    user.handleSetDestinationWordsBlackList()


@tg.message_handler(commands=['post_preview'])
@log_text
@user_finder
def handle_post(user, _, __=False):
  if user is not None:
    user.handlePostPreview()


@tg.message_handler(commands=['translate'])
@log_text
@user_finder
def handle_translate(user, _, __=False):
  if user is not None:
    user.handleTranslate()


@tg.message_handler(commands=['translate_to_message'])
@log_text
@user_finder
def handle_translate_to_message(user, _, __=False):
  if user is not None:
    user.handleTranslateToMessage()


@tg.message_handler(commands=['show_translations'])
@log_text
@user_finder
def handle_show_translations(user, _, __=False):
  if user is not None:
    user.handleShowTranslations()


@tg.message_handler(commands=['remove_translation'])
@log_text
@user_finder
def handle_remove_translation(user, _, __=False):
  if user is not None:
    user.handleRemoveTranslation()
    

@tg.message_handler(commands=['clear_translations'])
@log_text
@user_finder
def handle_clear_translations(user, _, __=False):
  if user is not None:
    user.handleClearTranslations()


# head and tail timesheet
@tg.message_handler(commands=['set_timesheet_head'])
@log_text
@user_finder
def handle_set_timesheet_head(user, _, __=False):
  if user is not None:
    user.handleSetTimesheetHead()


@tg.message_handler(commands=['set_timesheet_tail'])
@log_text
@user_finder
def handle_set_timesheet_tail(user, _, __=False):
  if user is not None:
    user.handleSetTimesheetTail()


@tg.message_handler(commands=['show_timesheet_list'])
@log_text
@user_finder
def handle_show_timesheet_list(user, _, __=False):
  if user is not None:
    user.handleShowTimesheetList()


# other
@tg.message_handler(content_types=['text', 'photo', 'video', 'audio'])
@log_text
@user_finder
def handle_message(user, m, __=False):
  if user is not None:
    # m.text = m.text or m.caption
    # if _is_forward_message(m):
    #   user.handleForwardMessage(m)
    # else:
    user.handleMessage(m)

  
@tg.callback_query_handler(func=lambda call: True)
def callback_query(call: CallbackQuery):
  user = users.find(call.from_user.id)
  if user is not None:
    user.handleCallbackQuery(call)
    
    
def _is_forward_message(m: Message):
  return m.forward_from is not None or m.forward_from_chat is not None


def set_my_commands():
  tg.set_my_commands(commands=[
    BotCommand(command=com.name, description=com.short)
    for com in commands
  ])