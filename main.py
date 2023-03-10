#!python3
import locale

from src import main


if __name__ == '__main__':
  locale.setlocale(
    category=locale.LC_ALL,
    locale="ru_RU"  # Note: do not use "de_DE" as it doesn't work
  )
  main()
