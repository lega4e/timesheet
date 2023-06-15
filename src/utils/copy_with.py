from copy import deepcopy


class CopyWith:
  def copyWith(self, **kwargs):
    cp = deepcopy(self)
    for key, value in kwargs.items():
      cp.__dict__[key] = value
    return cp