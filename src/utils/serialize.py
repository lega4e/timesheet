from abc import abstractmethod
from typing import Any


class Serializable:
  @abstractmethod
  def serialize(self) -> {str: Any}:
    pass
  
  @abstractmethod
  def deserialize(self, serialized: {str: Any}):
    pass