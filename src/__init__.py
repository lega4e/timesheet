import locale

from src.domain.locator import glob
from src.domain.tg.api import send_message
from src.domain.tg.tg_chat import TgChat
from src.entities.event.event import Event
from src.entities.message_maker.message_maker import get_event_line

locator = glob()
tg = locator.tg()
log = locator.flogger()
lira = locator.lira()
config = locator.config()


def clear_category(cat: str):
  for id in lira[cat]:
    lira.pop(id)
  lira.flush()

def set_password():
  for id in lira['timesheet']:
    tm = lira.get(id)
    tm['password'] = 'a6vbd3dks'
    lira.put(tm, id=id, cat='timesheet')
  lira.flush()

def set_locale():
  locale.setlocale(
    category=locale.LC_ALL,
    locale=config.locale(),
  )
  
def print_value(id):
  obj = lira.get(id=id)
  print(id, lira.cat(id))
  print(obj)
  
def set_value(value, id, cat):
  obj = lira.get(id=id)
  if obj is None:
    print('obj is None')
  else:
    lira.put(value, id=id, cat=cat)
    lira.flush()
    
def print_events():
  for lira_id in lira['event']:
    event = lira.get(id=lira_id)
    print(event['id'], event['desc'])
    
def print_lira_objs():
  for cat in lira.cats():
    print(cat)
    
def send_to_topic():
  send_message(tg=tg, text='Я убился!', chat_id=TgChat(type=TgChat.TOPIC,
                                                       chat_id=-1001620091980,
                                                       topic_id=21867,
                                                       message_id=24180))

def main():
  set_locale()
  locator.commandsManager().addHandlers()
  locator.commandsManager().setMenuCommands()
  log.info('Bot Started!')
  tg.infinity_polling(none_stop=True, interval=0)
