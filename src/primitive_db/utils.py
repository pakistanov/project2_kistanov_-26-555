import json
from pathlib import Path


def load_metadata(filepath):
    """Read table schemas, returning an empty database for a missing file."""
    try:
        with open(filepath, encoding="utf-8") as file:
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
    """Write UTF-8 JSON, replacing the original only after a complete write."""
    path = Path(filepath)
    temporary_path = path.with_name(path.name + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        file.write("\n")
    temporary_path.replace(path)
