import shlex

import prompt

from primitive_db.core import create_table, drop_table
from primitive_db.utils import load_metadata, save_metadata

METADATA_FILE = "db_meta.json"


def print_help():
    """Show the table commands and their arguments."""
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация")
    print("Типы столбцов: int, str, bool. Столбец ID:int добавляется автоматически.")


def run():
    """Load metadata and process commands until the user exits."""
    print("***База данных***")
    print_help()
    while True:
        try:
            metadata = load_metadata(METADATA_FILE)
        except (OSError, ValueError) as error:
            print(f"Ошибка загрузки метаданных: {error}")
            return
        try:
            user_input = prompt.string("\n>>>Введите команду: ")
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из программы.")
            return
        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue
        if not args:
            continue
        command, *arguments = args
        if command not in {"create_table", "drop_table", "list_tables", "help", "exit"}:
            print(f"Функции {command} нет. Попробуйте снова.")
            continue
        if command in {"help", "exit", "list_tables"} and arguments:
            print(f"Некорректное значение: {' '.join(arguments)}. Попробуйте снова.")
            continue
        previous_metadata = metadata.copy()
        if command == "exit":
            return
        if command == "help":
            print_help()
        elif command == "list_tables":
            if metadata:
                for table_name in metadata:
                    print(f"- {table_name}")
            else:
                print("Таблиц пока нет.")
        elif command == "create_table":
            if len(arguments) < 2:
                print("Ошибка: Формат команды: create_table <имя> <столбец:тип> ..")
                continue
            metadata = create_table(metadata, arguments[0], arguments[1:])
        elif command == "drop_table":
            if len(arguments) != 1:
                print("Ошибка: Формат команды: drop_table <имя_таблицы>")
                continue
            metadata = drop_table(metadata, arguments[0])
        if metadata != previous_metadata:
            try:
                save_metadata(METADATA_FILE, metadata)
            except OSError as error:
                print(f"Ошибка: Изменения не сохранены: {error}")
