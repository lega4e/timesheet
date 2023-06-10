from abc import abstractmethod


class LoggerStream:
  @abstractmethod
  def write(self, report: str) -> None:
    pass
