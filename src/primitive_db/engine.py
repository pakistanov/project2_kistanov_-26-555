import prompt
from prettytable import PrettyTable

from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    get_schema,
    insert,
    select,
    update,
    validate_clause,
)
from primitive_db.parser import (
    parse_set_clause,
    parse_values,
    parse_where_clause,
    tokenize,
)
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
    table_data_path,
)

METADATA_FILE = "db_meta.json"


def print_help():
    """Show table management and CRUD commands."""
    print("\n***Управление таблицами***")
    print("create_table <имя> <столбец:тип> ... - создать таблицу")
    print("list_tables - показать список таблиц")
    print("drop_table <имя> - удалить таблицу")
    print("\n***Операции с данными***")
    print("insert into <имя> values (<значение1>, ...) - добавить запись")
    print("select from <имя> [where <столбец> = <значение>] - прочитать записи")
    print("update <имя> set <столбец> = <значение> where <столбец> = <значение>")
    print("delete from <имя> where <столбец> = <значение> - удалить записи")
    print("info <имя> - информация о таблице")
    print("help - справка; exit - выход")
    print("Типы: int, str, bool. Строки — в кавычках. ID создаётся автоматически.")


def execute_data_command(metadata, command, arguments):
    """Parse a CRUD command, validate it, and read or save records."""
    if command == "insert":
        if len(arguments) < 5 or arguments[0] != "into" or arguments[2] != "values":
            raise ValueError("Формат: insert into <имя> values (<значение1>, ...).")
        table_name = arguments[1]
        values = parse_values(arguments[3:])
        data = insert(metadata, table_name, values)
        save_table_data(table_name, data)
        print(
            f'Запись с ID={data[-1]["ID"]} успешно добавлена в таблицу "{table_name}".'
        )
        return

    if command in {"select", "delete"}:
        if len(arguments) < 2 or arguments[0] != "from":
            raise ValueError(
                f"Формат: {command} from <имя> [where <столбец> = <значение>]."
            )
        table_name = arguments[1]
        if len(arguments) == 2 and command == "select":
            where_clause = None
        elif len(arguments) > 2 and arguments[2] == "where":
            where_clause = parse_where_clause(arguments[3:])
        else:
            raise ValueError("Укажите условие: where <столбец> = <значение>.")
        set_clause = None
    elif command == "update":
        if len(arguments) < 9 or arguments[1] != "set":
            raise ValueError(
                "Формат: update <имя> set <столбец> = <значение> where ..."
            )
        table_name = arguments[0]
        where_position = next(
            (
                index
                for index in range(5, len(arguments), 4)
                if arguments[index] == "where"
            ),
            None,
        )
        if where_position is None:
            raise ValueError("Укажите условие после where.")
        set_clause = parse_set_clause(arguments[2:where_position])
        where_clause = parse_where_clause(arguments[where_position + 1 :])
    else:
        if len(arguments) != 1:
            raise ValueError("Формат: info <имя_таблицы>.")
        table_name = arguments[0]
        set_clause = where_clause = None

    schema = get_schema(metadata, table_name)
    if where_clause is not None:
        validate_clause(metadata, table_name, where_clause)
    if set_clause is not None:
        validate_clause(metadata, table_name, set_clause)
    data = load_table_data(table_name)
    if command == "select":
        table = PrettyTable()
        table.field_names = list(schema)
        for row in select(data, where_clause):
            table.add_row([row[name] for name in schema])
        print(table)
    elif command == "info":
        print(f"Таблица: {table_name}")
        print("Столбцы: " + ", ".join(metadata[table_name]))
        print(f"Количество записей: {len(data)}")
    else:
        matching_rows = select(data, where_clause)
        if command == "update":
            changed_data = update(data, set_clause, where_clause)
        else:
            changed_data = delete(data, where_clause)
        save_table_data(table_name, changed_data)
        if not matching_rows:
            print("Записи по условию не найдены.")
        for row in matching_rows:
            if command == "update":
                print(
                    f'Запись с ID={row["ID"]} в таблице '
                    f'"{table_name}" успешно обновлена.'
                )
            else:
                print(
                    f'Запись с ID={row["ID"]} успешно удалена '
                    f'из таблицы "{table_name}".'
                )


def run():
    """Read commands and persist table schemas and records."""
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
            args = tokenize(user_input)
            if not args:
                continue
            command, *arguments = args
            if command in {"insert", "select", "update", "delete", "info"}:
                execute_data_command(metadata, command, arguments)
                continue
            if command not in {
                "create_table",
                "drop_table",
                "list_tables",
                "help",
                "exit",
            }:
                print(f"Функции {command} нет. Попробуйте снова.")
                continue
            if command in {"help", "exit", "list_tables"} and arguments:
                raise ValueError("Эта команда не принимает аргументы.")
            if command == "exit":
                return
            if command == "help":
                print_help()
            elif command == "list_tables":
                if not metadata:
                    print("Таблиц пока нет.")
                for table_name in metadata:
                    print(f"- {table_name}")
            elif command == "create_table":
                if len(arguments) < 2:
                    raise ValueError("Формат: create_table <имя> <столбец:тип> ...")
                table_name = arguments[0]
                existed = table_name in metadata
                create_table(metadata, table_name, arguments[1:])
                if not existed and table_name in metadata:
                    save_table_data(table_name, [])
                    save_metadata(METADATA_FILE, metadata)
            elif command == "drop_table":
                if len(arguments) != 1:
                    raise ValueError("Формат: drop_table <имя_таблицы>.")
                table_name = arguments[0]
                existed = table_name in metadata
                drop_table(metadata, table_name)
                if existed:
                    table_data_path(table_name).unlink(missing_ok=True)
                    save_metadata(METADATA_FILE, metadata)
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(f"Ошибка: {error}")
