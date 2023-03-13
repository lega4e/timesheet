from src.entities.user.user import User
from src.entities.user.user_factory import UserFactory
from src.utils.lira import Lira


class UserRepository:
  def __init__(
    self,
    user_factory: UserFactory,
    lira: Lira,
  ):
    self.userFactory = user_factory
    self.lira = lira
    self.users = self._deserializeUsers()

  def find(self, chat: int) -> User:
    if chat < 0:
      return None
    user = self.users.get(chat)
    if user is not None:
      return user[1]
    lira_id, user = self._makeUser(chat)
    self.users[chat] = (lira_id, user)
    return user
  
  def _makeUser(self, chat: int) -> (int, User):
    user = self.userFactory.make(chat=chat)
    user.addListener(self._onUserChanged)
    lira_id = self.lira.put(user.serialize(), cat='user')
    self.lira.flush()
    return lira_id, user

  def _deserializeUsers(self) -> {int : (int, User)}:
    users = {}
    for lira_id in self.lira['user']:
      user = self.userFactory.make(serialized=self.lira.get(id=lira_id))
      user.addListener(self._onUserChanged)
      users[user.chat] = (lira_id, user)
    return users
  
  def _onUserChanged(self, user: User):
    lira_id, user = self.users.get(user.chat)
    self.lira.put(user.serialize(), id=lira_id, cat='user')
    self.lira.flush()
