import locale

import src.domain.handlers as handlers
from src.domain.locator import glob

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


def main():
  set_locale()
  handlers.set_my_commands()
  log.info('Bot Started!')
  tg.polling(none_stop=True, interval=0)
