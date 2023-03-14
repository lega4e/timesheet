import locale
import traceback

import src.domain.handlers as handlers

from src.domain.di import glob


di = glob()
tg = di.tg()
log = di.flogger()
lira = di.lira()
config = di.config()


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


def main():
  set_locale()
  handlers.set_my_commands()
  log.info('Bot Started!')
  while True:
    try:
      tg.polling(none_stop=True, interval=0)
    except Exception:
      log.error(traceback.format_exc())
