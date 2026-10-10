# Primitive DB

Учебная консольная база данных на Python 3.12 и новее.

## Установка и запуск

Из корня проекта:

```powershell
uv sync
uv run database
```

Сборка и установка отдельного CLI-инструмента:

```powershell
uv build
uvx twine check dist/*
uv tool install --force .\dist\primitive_db-0.2.0-py3-none-any.whl
database
```

Если папка инструментов отсутствует в PATH, выполните `uv tool update-shell`
и откройте новый терминал. Команда `project` также поддерживается.

## Управление таблицами

| Команда | Действие |
| --- | --- |
| `create_table <имя> <столбец:тип> ...` | Создать таблицу |
| `list_tables` | Показать имена таблиц |
| `drop_table <имя>` | Удалить таблицу |
| `help` | Показать справку |
| `exit` | Завершить работу |

Поддерживаемые типы: `int`, `str`, `bool`. Имена таблиц и столбцов должны быть
допустимыми идентификаторами Python: например, `users`, `is_active`, `товары`.
Повторяющиеся столбцы запрещены. Столбец `ID:int` всегда стоит первым:
если он не указан, программа добавит его; явно указанный `ID:int` не дублируется.

Пример сеанса:

```text
>>>Введите команду: create_table users name:str age:int is_active:bool
Таблица "users" успешно создана со столбцами: ID:int, name:str, age:int, is_active:bool

>>>Введите команду: list_tables
- users

>>>Введите команду: drop_table users
Таблица "users" успешно удалена.

>>>Введите команду: exit
```

Структура таблиц сохраняется в `db_meta.json` в текущей рабочей папке.
При повторном запуске из той же папки таблицы сохраняются.
На этом этапе хранятся только имена таблиц и столбцы, без записей:

```json
{
    "users": ["ID:int", "name:str", "age:int", "is_active:bool"]
}
```

Повреждённый JSON вызывает сообщение об ошибке и завершение программы,
чтобы не перезаписать существующие данные.

## Проверка качества

```powershell
uv run ruff check .
uv run python -m unittest discover -s tests -v
```

## Демонстрация

[![Демонстрация установки и управления таблицами](https://asciinema.org/a/GPYm0pl7qpWV5dvI.svg)](https://asciinema.org/a/GPYm0pl7qpWV5dvI)

Запись реального сеанса Windows-терминала: установка пакета, запуск,
создание, просмотр и удаление таблицы. Исходная запись: [table-management.cast](docs/table-management.cast).
