class Emoji:
  EDIT = '✍️' # ✏️️💉
  WARNING = '⚠️'
  BANANA = '🍌'
  SWORD = '⚔️'
  FAIL = '🥺'
  TIMESHEET_ITEM = '👏'
  THINK = '🤔'
  COMMAND = '🎯'
  STRAWBERRY = '🍓'
  CAKE = '🍰'
  OFFICER = '🫡'
  SPIKE='🖖'
  
def get_emoji(emoji: str = None):
  return {
    'edit': Emoji.EDIT,
    'warning': Emoji.WARNING,
    'ok': Emoji.BANANA,
    'fail': Emoji.FAIL,
    'think': Emoji.THINK,
    'info': Emoji.STRAWBERRY,
    'infoglob': Emoji.CAKE,
    'translation': Emoji.OFFICER,
    'place': Emoji.SPIKE,
  }.get(emoji)
