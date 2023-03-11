class Emoji:
  EDIT = '✍️' # ✏️️💉
  WARNING = '⚠️'
  BANANA = '🍌'
  SWORD = '⚔️'
  FAIL = '🥺'
  TIMESHEET_ITEM = '👏'
  
def emoji(text: str, edit=False, warning=False, ok=False, fail=False):
  e = (Emoji.EDIT if edit else
       Emoji.WARNING if warning else
       Emoji.BANANA if ok else
       Emoji.FAIL if fail else
       None)
  return f'{e} {text}' if e is not None else text
