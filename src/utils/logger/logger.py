from logging import Logger


class FLogger:
    def __init__(self, logger: Logger):
        self.logger = logger

    def info(self, message, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)

    def text(self, m, *args, **kwargs):
        self.info(f'[@{FLogger._usernameIdOrId(m)}] {m.text}', *args, **kwargs)

    def answer(self, chat_id: int, text: str, *args, **kwargs):
        self.info(f'[{chat_id}]\n{text}', *args, **kwargs)

    @staticmethod
    def _usernameIdOrId(m):
        return (f'{m.chat.username}|{m.chat.id}'
                if m.chat.username is not None
                else m.chat.id)
