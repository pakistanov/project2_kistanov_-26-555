"""Shared configuration, value types, and command grammar."""

META_FILE = "db_meta.json"
DATA_DIR = "data"
JSON_EXTENSION = ".json"
TEMP_EXTENSION = ".tmp"
ENCODED_NAME_PREFIX = "~"
WINDOWS_RESERVED_NAMES = {"con", "prn", "aux", "nul"} | {
    f"{prefix}{number}" for prefix in ("com", "lpt") for number in range(1, 10)
}
INT_TYPE = "int"
PYTHON_TYPES = {INT_TYPE: int, "str": str, "bool": bool}
VALID_TYPES = set(PYTHON_TYPES)
ID_COLUMN = "ID"
DEFAULT_ID_SCHEMA = f"{ID_COLUMN}:{INT_TYPE}"
TEXT_ENCODING = "utf-8"
JSON_INDENT = 4
INVALID_VALUE_MESSAGE = "Некорректное значение: {value}. Попробуйте снова."
NO_MATCH_MESSAGE = "Записи по условию не найдены."
COMMAND_PUNCTUATION = "(),="
ASSIGNMENT_TOKEN_COUNT = 3
SET_ASSIGNMENT_STRIDE = ASSIGNMENT_TOKEN_COUNT + 1
SET_CLAUSE_START = 2
UPDATE_WHERE_START = SET_CLAUSE_START + ASSIGNMENT_TOKEN_COUNT
MIN_UPDATE_ARGUMENTS = UPDATE_WHERE_START + 1 + ASSIGNMENT_TOKEN_COUNT
INSERT_VALUES_START = 3
MIN_INSERT_ARGUMENTS = INSERT_VALUES_START + 2
MIN_QUERY_ARGUMENTS = 2
QUERY_WHERE_INDEX = MIN_QUERY_ARGUMENTS
QUERY_CONDITION_START = QUERY_WHERE_INDEX + 1
DATA_COMMANDS = {"insert", "select", "update", "delete", "info"}
TABLE_COMMANDS = {"create_table", "drop_table", "list_tables", "help", "exit"}
HELP_TEXT = (
    "***Процесс работы с таблицей***\nФункции:\n"
    "<command> create_table <имя_таблицы> <столбец1:тип> ... - создать таблицу\n"
    "<command> list_tables - показать список всех таблиц\n"
    "<command> drop_table <имя_таблицы> - удалить таблицу\n"
    "\n***Операции с данными***\nФункции:\n"
    "<command> insert into <имя_таблицы> values (<значение1>, ...) - создать запись\n"
    "<command> select from <имя_таблицы> where <столбец> = <значение> "
    "- прочитать записи по условию\n"
    "<command> select from <имя_таблицы> - прочитать все записи\n"
    "<command> update <имя_таблицы> set <столбец> = <новое_значение> "
    "where <столбец> = <значение> - обновить запись\n"
    "<command> delete from <имя_таблицы> where <столбец> = <значение> "
    "- удалить запись\n"
    "<command> info <имя_таблицы> - вывести информацию о таблице\n"
    "<command> help - справочная информация\n"
    "<command> exit - выход из программы"
)
