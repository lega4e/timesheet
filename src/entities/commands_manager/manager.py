from telebot.types import BotCommand, CallbackQuery, Message

from src.domain.locator import LocatorStorage, Locator
from src.entities.commands_manager.commands import global_command_list


class CommandsManager(LocatorStorage):
  def __init__(self, locator: Locator):
    super().__init__(locator)
    self.tg = locator.tg()
    self.userRepo = self.locator.userRepo()
    self.logger = self.locator.flogger()


  # decorators
  def findUserDecorator(self, func):
    def wrapper(m, res=False):
      func(self.userRepo.find(m.chat.id) if m.chat.id > 0 else None, m, res)
    return wrapper

  def logCommandDecorator(self, func):
    def wrapper(m, res=False):
      self.logger.text(m)
      func(m, res)
  
    return wrapper

  def logMessageDecorator(self, func):
    def wrapper(m: Message, res=False):
      if m.chat.id > 0:
        self.logger.text(m)
      func(m, res)
    return wrapper
  
  
  # handlers
  def addHandlers(self):
    self.addCommandHandlers()
    self.addMessageHandlers()
    self.addCallbackQueryHandlers()
    
  def addCommandHandlers(self):
    for command in global_command_list:
      exec(f'''
@self.tg.message_handler(commands=[command.name])
@self.logCommandDecorator
@self.findUserDecorator
def handle_{command.name}(user, _, __):
  if user is not None:
    exec(f'user.{command.userCommand}()')
      ''')
      
  def addMessageHandlers(self):
    @self.tg.message_handler(content_types=['text']) #, 'photo', 'video', 'audio'])
    @self.logMessageDecorator
    @self.findUserDecorator
    def handle_message(user, m, __=False):
      if user is not None:
        user.handleMessage(m)
      
  def addCallbackQueryHandlers(self):
    @self.tg.callback_query_handler(func=lambda call: True)
    def handle_callback_query(q: CallbackQuery):
      user = self.userRepo.find(q.from_user.id)
      if user is not None:
        user.handleCallbackQuery(q)
        
        
  # menu
  def setMenuCommands(self):
    self.tg.set_my_commands(commands=[
    BotCommand(command=com.name, description=com.short)
    for com in global_command_list
    if com.addToMenu
  ])
