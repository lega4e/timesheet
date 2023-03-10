from copy import copy
from typing import Callable, Any


class Notifier:
  def __init__(self):
    self._listeners: {int: (Any, Callable)} = {}
    self._counter = 0
    
  def addListener(self, callback: Callable, event = None) -> Callable:
    if not isinstance(event, list):
      self._counter += 1
      self._listeners[self._counter] = (event, callback)
      counter = copy(self._counter)
      return lambda: self._listeners.pop(counter)
    dispose_funs = [self.addListener(callback, e) for e in event]
    def dispose():
      for d in dispose_funs:
        d()
    return dispose
  
  def notify(self, event = None, *args, **kwargs):
    for e, callback in self._listeners.values():
      if e == event:
        callback(self, *args, **kwargs)