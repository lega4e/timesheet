class Emoji:
  EDIT = '✍️' # ✏️️💉
  WARNING = '⚠️'
  BANANA = '🍌'
  SWORD = '⚔️'
  FAIL = '🥺'
  TIMESHEET_ITEM = '👏'
  THINK = '🤔'
  COMMAND = '🎯'
  
def get_emoji(emoji: str = None):
  return {
    'edit': Emoji.EDIT,
    'warning': Emoji.WARNING,
    'ok': Emoji.BANANA,
    'fail': Emoji.FAIL,
    'think': Emoji.THINK,
  }.get(emoji)
