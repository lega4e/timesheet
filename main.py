#!python3
import locale

from src import main


# TODO:
# - set_channel не распознаёт ссылки
# - распознавание t.me ссылок
# - Пропуск или ноне, сообщение об этом
# - Убрать "мероприятие создано"
# - Пропуск длительности
# - Писать id мероприятия после создания
# - Параметр: писать окончание мероприятия
# - post_preview_with_id
if __name__ == '__main__':
  locale.setlocale(
    category=locale.LC_ALL,
    locale="ru_RU"  # Note: do not use "de_DE" as it doesn't work
  )
  main()
