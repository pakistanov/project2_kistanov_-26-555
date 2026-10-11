import json
import os

from primitive_db.constants import (
    DATA_DIR,
    ENCODED_NAME_PREFIX,
    INVALID_VALUE_MESSAGE,
    JSON_EXTENSION,
    JSON_INDENT,
    META_FILE,
    TEMP_EXTENSION,
    TEXT_ENCODING,
    WINDOWS_RESERVED_NAMES,
)


def valid_table_name(table_name):
    """Allow only nonempty ASCII letters, digits, and underscores."""
    return (
        bool(table_name)
        and table_name.isascii()
        and all(character.isalnum() or character == "_" for character in table_name)
    )


def load_metadata(filepath):
    """Read schemas, returning an empty database for a missing file."""
    try:
        with open(filepath, encoding=TEXT_ENCODING) as file:
            data = json.load(file)
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Метаданные должны быть JSON-объектом.")
    for name, columns in data.items():
        if not isinstance(columns, list) or not all(
            isinstance(column, str) for column in columns
        ):
            raise ValueError(f'Некорректная структура таблицы "{name}".')
    return data


def save_metadata(filepath, data):
    """Replace a JSON file only after writing its new contents completely."""
    path = os.fspath(filepath)
    temporary_path = path + TEMP_EXTENSION
    with open(temporary_path, "w", encoding=TEXT_ENCODING) as file:
        json.dump(data, file, ensure_ascii=False, indent=JSON_INDENT)
        file.write("\n")
    os.replace(temporary_path, path)


def table_data_path(table_name):
    """Keep case-sensitive table names distinct on every supported filesystem."""
    if not valid_table_name(table_name):
        raise ValueError(INVALID_VALUE_MESSAGE.format(value=table_name))
    filename = table_name
    if table_name != table_name.lower() or table_name in WINDOWS_RESERVED_NAMES:
        filename = ENCODED_NAME_PREFIX + table_name.encode("ascii").hex()
    return os.path.join(DATA_DIR, filename + JSON_EXTENSION)


def load_table_data(table_name):
    """Load records, returning an empty list when the file is missing."""
    try:
        with open(table_data_path(table_name), encoding=TEXT_ENCODING) as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise ValueError(f'Некорректные данные таблицы "{table_name}".')
    return data


def save_table_data(table_name, data):
    """Atomically replace a table's JSON records."""
    path = table_data_path(table_name)
    os.makedirs(DATA_DIR, exist_ok=True)
    save_metadata(path, data)


def remove_table_data(table_name):
    """Remove a table's data file if it exists."""
    try:
        os.remove(table_data_path(table_name))
    except FileNotFoundError:
        pass


def persist_table_creation(previous_metadata, metadata, table_name):
    """Save a new schema and empty data, restoring schemas if data saving fails."""
    save_metadata(META_FILE, metadata)
    try:
        save_table_data(table_name, [])
    except OSError:
        save_metadata(META_FILE, previous_metadata)
        raise


def persist_table_removal(previous_metadata, metadata, table_name):
    """Save schemas before deletion, restoring them if removal fails."""
    save_metadata(META_FILE, metadata)
    try:
        remove_table_data(table_name)
    except OSError:
        save_metadata(META_FILE, previous_metadata)
        raise
