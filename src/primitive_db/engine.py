import json

import prompt
from prettytable import PrettyTable

from primitive_db.constants import (
    DATA_COMMANDS,
    HELP_TEXT,
    ID_COLUMN,
    META_FILE,
    NO_MATCH_MESSAGE,
    TABLE_COMMANDS,
)
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
from primitive_db.decorators import create_cacher, handle_db_errors
from primitive_db.parser import (
    invalid_value,
    parse_insert_command,
    parse_query_command,
    parse_update_command,
    tokenize,
)
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    persist_table_creation,
    persist_table_removal,
    save_table_data,
)

cache_result = create_cacher()


def reset_cache():
    """Discard cached queries after successfully persisted changes."""
    global cache_result
    cache_result = create_cacher()


def select_rows(table_name, table_data, where_clause=None):
    """Cache a selection by exact table name and a stable condition string."""
    key = (table_name, json.dumps(where_clause, sort_keys=True, ensure_ascii=False))
    rows = cache_result(key, lambda: select(table_data, where_clause))
    return None if rows is None else [row.copy() for row in rows]


def print_help():
    """Show all table management, CRUD, and general commands."""
    print("\n" + HELP_TEXT)


def print_records(schema, rows):
    """Render records with the schema's original column order."""
    table = PrettyTable()
    table.field_names = list(schema)
    for row in rows:
        table.add_row([row[name] for name in schema])
    print(table)


def execute_insert(metadata, arguments):
    """Load data, add one record, and report success after saving."""
    table_name, values = parse_insert_command(arguments)
    if get_schema(metadata, table_name) is None:
        return
    data = load_table_data(table_name)
    changed_data = insert(metadata, table_name, data, values)
    if changed_data is None:
        return
    save_table_data(table_name, changed_data)
    reset_cache()
    print(
        f"Запись с ID={changed_data[-1][ID_COLUMN]} успешно добавлена "
        f'в таблицу "{table_name}".'
    )


def execute_changes(command, table_name, data, where_clause, set_clause=None):
    """Select affected IDs before updating or requesting deletion confirmation."""
    matching_rows = select_rows(table_name, data, where_clause)
    if matching_rows is None:
        return
    if not matching_rows:
        print(NO_MATCH_MESSAGE)
        return
    if command == "update":
        changed_data = update(data, set_clause, where_clause)
    else:
        changed_data = delete(data, where_clause)
    if changed_data is None:
        return
    save_table_data(table_name, changed_data)
    reset_cache()
    for row in matching_rows:
        if command == "update":
            print(
                f'Запись с ID={row[ID_COLUMN]} в таблице "{table_name}" '
                "успешно обновлена."
            )
        else:
            print(
                f"Запись с ID={row[ID_COLUMN]} успешно удалена "
                f'из таблицы "{table_name}".'
            )


@handle_db_errors
def execute_data_command(metadata, command, arguments):
    """Parse and validate a data command before dispatching its operation."""
    if command == "insert":
        execute_insert(metadata, arguments)
        return
    set_clause = None
    if command in {"select", "delete"}:
        table_name, where_clause = parse_query_command(
            arguments, allow_without_where=command == "select"
        )
    elif command == "update":
        table_name, set_clause, where_clause = parse_update_command(arguments)
        if ID_COLUMN in set_clause:
            raise ValueError("Ошибка: Изменение столбца ID запрещено.")
    else:
        if len(arguments) != 1:
            raise invalid_value(arguments)
        table_name = arguments[0]
        where_clause = None
    schema = get_schema(metadata, table_name)
    if schema is None:
        return
    for clause in (where_clause, set_clause):
        if clause is not None and validate_clause(metadata, table_name, clause) is None:
            return
    data = load_table_data(table_name)
    if command == "select":
        rows = select_rows(table_name, data, where_clause)
        if rows is not None:
            print_records(schema, rows)
    elif command == "info":
        print(f"Таблица: {table_name}")
        print("Столбцы: " + ", ".join(metadata[table_name]))
        print(f"Количество записей: {len(data)}")
    else:
        execute_changes(command, table_name, data, where_clause, set_clause)


def execute_create_table(metadata, arguments):
    """Persist a new schema and empty data before printing success."""
    if len(arguments) < 2:
        raise invalid_value(arguments)
    table_name = arguments[0]
    result = create_table(metadata.copy(), table_name, arguments[1:])
    if result is None:
        return
    persist_table_creation(metadata, result, table_name)
    metadata.clear()
    metadata.update(result)
    reset_cache()
    print(
        f'Таблица "{table_name}" успешно создана со столбцами: '
        + ", ".join(result[table_name])
    )


def execute_drop_table(metadata, arguments):
    """Validate existence before confirmation and report only persisted removal."""
    if len(arguments) != 1:
        raise invalid_value(arguments)
    table_name = arguments[0]
    if get_schema(metadata, table_name) is None:
        return
    result = drop_table(metadata.copy(), table_name)
    if result is None:
        return
    persist_table_removal(metadata, result, table_name)
    metadata.clear()
    metadata.update(result)
    reset_cache()
    print(f'Таблица "{table_name}" успешно удалена.')


@handle_db_errors
def execute_command(metadata, user_input):
    """Execute a command, returning False only for a valid exit command."""
    args = tokenize(user_input)
    if not args:
        return True
    command, *arguments = args
    if command in DATA_COMMANDS:
        execute_data_command(metadata, command, arguments)
    elif command not in TABLE_COMMANDS:
        print(f"Функции {command} нет. Попробуйте снова.")
    elif command in {"help", "exit", "list_tables"}:
        if arguments:
            raise invalid_value(arguments)
        if command == "exit":
            return False
        if command == "help":
            print_help()
        else:
            for table_name in metadata:
                print(f"- {table_name}")
    elif command == "create_table":
        execute_create_table(metadata, arguments)
    else:
        execute_drop_table(metadata, arguments)
    return True


def run():
    """Read commands with current schemas and persist successful operations."""
    reset_cache()
    print("***База данных***")
    print_help()
    while True:
        try:
            metadata = load_metadata(META_FILE)
        except (OSError, ValueError) as error:
            print(f"Ошибка загрузки метаданных: {error}")
            return
        try:
            user_input = prompt.string("\n>>>Введите команду: ")
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из программы.")
            return
        if execute_command(metadata, user_input) is False:
            return
