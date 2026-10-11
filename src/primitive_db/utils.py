import json
import os

from primitive_db.constants import DATA_DIR, JSON_INDENT, TEXT_ENCODING


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
    temporary_path = path + ".tmp"
    with open(temporary_path, "w", encoding=TEXT_ENCODING) as file:
        json.dump(data, file, ensure_ascii=False, indent=JSON_INDENT)
        file.write("\n")
    os.replace(temporary_path, path)


def table_data_path(table_name):
    """Return the JSON path for a valid table name."""
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {table_name}.")
    return os.path.join(DATA_DIR, f"{table_name}.json")


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
    """Save records to data/<table_name>.json."""
    path = table_data_path(table_name)
    os.makedirs(DATA_DIR, exist_ok=True)
    save_metadata(path, data)


def remove_table_data(table_name):
    """Remove a table's data file if it exists."""
    try:
        os.remove(table_data_path(table_name))
    except FileNotFoundError:
        pass
