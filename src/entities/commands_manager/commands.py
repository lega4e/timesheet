class CommandDescription:
  def __init__(
    self,
    name: str,
    preview: str,
    user_command: str,
    short: str,
    long: str,
    add_to_menu: bool = True,
  ):
    self.name = name
    self.preview = preview
    self.userCommand = user_command
    self.short = short
    self.long = long
    self.addToMenu = add_to_menu or True
 
# Как будет выглядеть страничка
#
# Новое событие /make_event
# Добавляет новое событие в подключённое расписание
#
# Группы команд
# (1) Мероприятия
#     - новое
#     - повторить
#     - удалить
#     - редактировать
#     - посмотреть все
#
# (2) Канал
#     - покавать
#     - установить
#     - запостить расписание
#     - транслировать в конкретное сообщение
#     - показать все автопосты
#     - удалить автопост
#     - новый автопост
#     - изменить параметры
#       - заголовок
#       - подвал
#       - чёрный список айди
#       - чёрный список слов
#       - фромат вывода
#
# (3) Расписание
#     - новое
#     - установить
#     - посмотреть места
#     - установить места
#     - посмотреть оргов
#     - установить оргов
#     - показать все трансляции
#     - удалить трансляцию
#     - удалить все трансляции
#     - изменить параметры (см. канал: те же самые)
#
# (X) Прочее
#     - список команд (помощь)

global_command_list = [
  CommandDescription(*params)
  for params in [
    (
      'help',
      '/help',
      'handleHelp',
      'Помощь',
      'Показывает страницу с подробным объяснением команд',
      True,
    ),
    (
      'commands',
      '/commands',
      'handleCommands',
      'События',
      'Показывает страницу с действиями над событиями',
      True,
    ),
    (
      'events',
      '/events',
      'handleEvents',
      'События',
      'Показывает страницу с действиями над событиями',
      True,
    ),
    (
      'destination',
      '/destination',
      'handleDestination',
      'Канал',
      'Показывает страницу с действиями над каналом',
      True,
    ),
    (
      'autoposts',
      '/autoposts',
      'handleAutoposts',
      'Автопосты',
      'Показывает страницу с действиями над автопостами для данного расписания',
      True,
    ),
    (
      'timesheet',
      '/timesheet',
      'handleTimesheet',
      'Расписание',
      'Показывает страницу с действиями над расписанием',
      True,
    ),
    (
      'translations',
      '/translations',
      'handleTranslations',
      'Трансляции',
      'Показывает страницу с действиями над трансляциями для данного расписания',
      True,
    ),
    (
      'places_and_orgs',
      '/places_and_orgs',
      'handlePlacesAndOrgs',
      'Места и организаторы',
      'Показывает страницу с действиями над местами и организаторами для данного расписания',
      True,
    ),
    (
      'make_event',
      '/make_event',
      'handleMakeEvent',
      'Новое событие',
      'Добавляет новое событие в подключённое расписание',
      True,
    ),
    (
      'replay',
      '/replay',
      'handleReplay',
      'Повторить мероприятие',
      'Повторяет мероприятие, т.е. создаёт мероприятие с тем же названием, организатором и местом, с временем начала на неделю позже',
      True,
    ),
    (
      'edit_event',
      '/edit_event',
      'handleEditEvent',
      'Редактировать событие',
      'Открывает диалог для редактирования выбранного события, принадлежащее подключённому расписанию. Событие выбирается с помощью идентификатора; чтобы узнать идентификатор события, используйте команду /show_events',
      True,
    ),
    (
      'remove_event',
      '/remove_event',
      'handleRemoveEvent',
      'Удалить событие',
      'Удаляет из подключённого расписание событие с указаным идентификатором. Идентификатор события можно узнать с помощью команды /show_events',
      True,
    ),
    (
      'post_preview',
      '/post_preview',
      'handlePostPreview',
      'Превью расписания',
      'Отправить пост расписания не в канал, а в чат с вами',
      True,
    ),
    (
      'translate',
      '/translate',
      'handleTranslate',
      'Запостить расписание',
      'Постит расписание в канал и держит текст актуальным (реагирует на любые операции изменяющие расписания)',
      True,
    ),
    (
      'translate_to_message',
      '/translate_to_message',
      'handleTranslateToMessage',
      'Транслировать в сообщение',
      'Редактирует указанное сообщение и держит его в актуальном состоянии',
      True,
    ),
    (
      'make_timesheet',
      '/make_timesheet',
      'handleMakeTimesheet',
      'Создать расписание',
      'Создаёт новое расписание с указаным именем и паролем. Имя и пароль будут использоваться для подключения к расписанию с помощью команды /set_timesheet. Подключиться к расписанию может любой пользователь',
      True,
    ),
    (
      'set_timesheet',
      '/set_timesheet',
      'handleSetTimesheet',
      'Подключиться к расписанию',
      'Подключает к расписанию с указаным именем. Для защиты используется пароль: спросите его у создателя расписания',
      True,
    ),
    (
      'show_destination',
      '/show_destination',
      'handleShowDestination',
      'Посмотреть канал',
      'Показывает канал или публичную группу, в который бот постит расписание и держит его актуальным',
      True,
    ),
    (
      'set_destination',
      '/set_destination',
      'handleSetDestination',
      'Подключиться к каналу',
      'Устанавливает канал или публичную группу, в который бот будет постить расписание и держать его актуальным',
      True,
    ),
    (
      'show_timesheet_info',
      '/show_timesheet_info',
      'handleShowTimesheetInfo',
      'Параметры расписания',
      'Показывает всю информацию о подключённом расписаниии',
      True,
    ),
    (
      'show_destination_info',
      '/show_destination_info',
      'handleShowDestinationInfo',
      'Параметры канала',
      'Показывает всю информацию о текущем подключении (канале или группе)',
      True,
    ),
    (
      'show_events',
      '/show_events',
      'handleShowEvents',
      'Посмотреть события',
      'Показывает в кратком виде все события, принадлежащие подключённому расписанию; здесь можно узнать id события (предваряется решёткой "#") для команд /edit_event и /remove_event',
      True,
    ),
    (
      'set_destination_head',
      '/set_destination_head',
      'handleSetDestinationHead',
      'Заголовок для канала',
      'Устанавливает специфичный для текущего канала или группы специфичный заголовок; для остальных каналов будет браться заголовок, установленный командой /set_timesheet_head',
      True,
    ),
    (
      'set_destination_tail',
      '/set_destination_tail',
      'handleSetDestinationTail',
      'Подвал для канала',
      'Устанавливает специфичный для текущего канала или группы специфичный подвал; для остальных каналов будет браться подвал, установленный командой /set_timesheet_tail',
      True,
    ),
    (
      'set_destination_black_list',
      '/set_destination_black_list',
      'handleSetDestinationBlackList',
      'Скрыть мероприятия по ID',
      'Задаёт список мероприятий, которые не должны отображаться в текущем канале или группе',
      True,
    ),
    (
      'set_destination_words_black_list',
      '/set_destination_words_black_list',
      'handleSetDestinationWordsBlackList',
      'Установить бан-слова',
      'Если название мероприятие будет содержать одно из перечисленных слов, устанавливающихся этой командой, мероприятие не будет показано в расписании в данном канале или группе',
      True,
    ),
    (
      'set_timesheet_head',
      '/set_timesheet_head',
      'handleSetTimesheetHead',
      'Заголовок расписания',
      'Устанавливает текст, который будет находиться в начале поста с расписанием. Введите специальное значение "none" для удаления',
      True,
    ),
    (
      'set_timesheet_tail',
      '/set_timesheet_tail',
      'handleSetTimesheetTail',
      'Подвал расписания',
      'Устанавливает текст, который будет находиться в конце поста с расписанием. Введите специальное значение "none" для удаления',
      True,
    ),
    (
      'show_timesheet_list',
      '/show_timesheet_list',
      'handleShowTimesheetList',
      'Все расписания',
      'Отображает список названий всех существующих расписаний',
      True,
    ),
    (
      'clear_translations',
      '/clear_translations',
      'handleClearTranslations',
      'Очистить трансляции',
      'Отключает поддержание постов в канале в актуальном состоянии',
      True,
    ),
    (
      'set_timesheet_event_format',
      '/set_timesheet_event_format',
      'handleSetTimesheetEventFormat',
      'Формат события',
      'Устанавливает формат события для расписания',
      True,
    ),
    (
      'set_destination_event_format',
      '/set_destination_event_format',
      'handleSetDestinationEventFormat',
      'Формат события',
      'Устанавливает формат события для канала',
      True,
    ),
    (
      'show_translations',
      '/show_translations',
      'handleShowTranslations',
      'Показать трансляции',
      'Показывает все трансляции для данного расписания во все каналы',
      True,
    ),
    (
      'remove_translation',
      '/remove_translation',
      'handleRemoveTranslation',
      'Удалить трансляцию',
      'Удалить трансляцию по ID; используйте /show_translations, чтобы узнать ID',
      True,
    ),
    (
      'show_places',
      '/show_places',
      'handleShowPlaces',
      'Показать места',
      'Показывает все места; их список используются для кнопок при создании и редактировании события',
      True,
    ),
    (
      'set_places',
      '/set_places',
      'handleSetPlaces',
      'Установить места',
      'Установить список мест; он используются для кнопок при создании и редактировании события',
      True,
    ),
    (
      'show_orgs',
      '/show_orgs',
      'handleShowOrgs',
      'Показать организаторов',
      'Показывает всех организаторов; их список используются для кнопок при создании и редактировании события',
      True,
    ),
    (
      'set_orgs',
      '/set_orgs',
      'handleSetOrgs',
      'Установить организаторов',
      'Устанавливает список организаторов; они используются для кнопок при создании и редактировании события',
      True,
    ),
    (
      'start',
      '/start',
      'handleStart',
      'Запуск',
      'Выполняется в тот момент, когда вы впервые запускаете бота; но можно повторить :)',
      True,
    ),
    (
      'make_autopost',
      '/make_autopost',
      'handleMakeAutopost',
      'Новый автопост',
      'Создаёт новый автопост в текущий канал: через определённые промежутки времени расписатель будет постить новое расписание и отключать трансляцию старого',
      True,
    ),
    (
      'show_autoposts',
      '/show_autoposts',
      'handleShowAutoposts',
      'Показать автопосты',
      'Показывает все существующие автопосты для данного расписания во все каналы',
      True,
    ),
    (
      'remove_autopost',
      '/remove_autopost',
      'handleRemoveAutopost',
      'Удалить автопост',
      'Удаляет автопост; чтобы узнать ID, используйте /show_autoposts',
      True,
    ),
  ]
]
