#!python3
import locale

from src import main


# TODO:
# - Пропуск или ноне, сообщение об этом
# - post_preview_with_id
if __name__ == '__main__':
  locale.setlocale(
    category=locale.LC_ALL,
    locale="ru_RU"
  )
  main()
