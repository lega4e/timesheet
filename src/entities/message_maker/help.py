from src.entities.message_maker.piece import Piece


help_head = [
  Piece('Расписатель', type='bold'),
  Piece('\n\n'),
  Piece('Этот бот 🤖 предназначен для составления расписания '
        'событий 🎉 и автоматического редактирования постов 📝 в канале '
        'таким образом, чтобы они всегда отображали актуальное состояние 🤗 '
        'Пользуйтесь 😊')
]

help_tail = [
  Piece('Бот создан by '),
  Piece('Черский', url='https://t.me/lega4e'),
  Piece(', исходный код '),
  Piece('здесь', url='https://github.com/nvxden/timesheet'),
  Piece('. Подписывайтесь на '),
  Piece('канал', url='https://t.me/lega4e_channel'),
  Piece(', чтобы побольше узнать про коммунарскую жизнь :))'),
]
