import json

from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from primitive_db.utils import load_table_data

SUPPORTED_TYPES = {"int", "str", "bool"}
cache_result = create_cacher()


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Validate a table schema and add it to the metadata."""
    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {table_name}.")
    if not columns:
        raise ValueError("Укажите хотя бы один столбец в формате имя:тип.")
    schema = ["ID:int"]
    names = set()
    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            raise ValueError(f"Некорректный столбец: {column}.")
        name, data_type = parts
        if not name.isidentifier() or data_type not in SUPPORTED_TYPES:
            raise ValueError(f"Некорректный столбец или тип: {column}.")
        normalized_name = "ID" if name.upper() == "ID" else name
        if normalized_name in names:
            raise ValueError(f'Столбец "{normalized_name}" указан несколько раз.')
        names.add(normalized_name)
        if normalized_name == "ID":
            if data_type != "int":
                raise ValueError("Столбец ID должен иметь тип int.")
        else:
            schema.append(column)
    metadata[table_name] = schema
    print(f'Таблица "{table_name}" успешно создана со столбцами: ' + ", ".join(schema))
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Remove an existing table after user confirmation."""
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')
    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


@handle_db_errors
def get_schema(metadata, table_name):
    """Return column names and types for an existing table."""
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')
    return dict(column.split(":") for column in metadata[table_name])


@handle_db_errors
def validate_clause(metadata, table_name, clause):
    """Return True for valid fields or None after reporting an error."""
    schema = get_schema(metadata, table_name)
    if schema is None:
        return None
    python_types = {"int": int, "str": str, "bool": bool}
    for name, value in clause.items():
        if name not in schema:
            raise KeyError(name)
        if type(value) is not python_types[schema[name]]:
            raise ValueError(
                f'Столбец "{name}" требует тип {schema[name]}, '
                f"получено значение {value!r}."
            )
    return True


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Validate values and append a record with an automatically generated ID."""
    schema = get_schema(metadata, table_name)
    if schema is None:
        return None
    columns = [name for name in schema if name != "ID"]
    if len(values) != len(columns):
        raise ValueError(
            f"Ожидается {len(columns)} значений без ID, получено {len(values)}."
        )
    record = dict(zip(columns, values))
    if validate_clause(metadata, table_name, record) is None:
        return None
    data = load_table_data(table_name)
    new_id = max((row["ID"] for row in data), default=0) + 1
    data.append({"ID": new_id, **record})
    return data


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Cache equal queries against the same contents of a table."""
    key = (
        json.dumps(table_data, sort_keys=True, ensure_ascii=False),
        None if where_clause is None else tuple(sorted(where_clause.items())),
    )

    def find_rows():
        return [
            row.copy()
            for row in table_data
            if where_clause is None
            or all(row.get(name) == value for name, value in where_clause.items())
        ]

    return [row.copy() for row in cache_result(key, find_rows)]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Update matching records and return the changed table data."""
    matching_rows = [
        row
        for row in table_data
        if all(row.get(name) == value for name, value in where_clause.items())
    ]
    if "ID" in set_clause and matching_rows:
        new_id = set_clause["ID"]
        other_ids = [row["ID"] for row in table_data if row not in matching_rows]
        if new_id < 1 or len(matching_rows) > 1 or new_id in other_ids:
            raise ValueError("ID должен быть положительным и уникальным.")
    for row in matching_rows:
        row.update(set_clause)
    return table_data


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data, where_clause):
    """Remove matching records after user confirmation."""
    return [
        row
        for row in table_data
        if not all(row.get(name) == value for name, value in where_clause.items())
    ]
