from typing import Callable, Iterable, Any


def reduce_list(fun: Callable, iterable: Iterable, start: Any):
  for value in iterable:
    start = fun(start, value)
  return start


def insert_between(values: [], term) -> []:
  if len(values) == 0:
    return values
  result = [values[0]]
  for value in values[1:]:
    result.extend([term, value])
  return result
