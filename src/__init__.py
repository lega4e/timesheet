import src.domain.handlers as handlers

from src.domain.di import glob


di = glob()
tg = di.tg()
log = di.flogger()
lira = di.lira()


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


def main():
  handlers.set_my_commands()
  log.info('Bot Started!')
  tg.polling(none_stop=True, interval=0)
