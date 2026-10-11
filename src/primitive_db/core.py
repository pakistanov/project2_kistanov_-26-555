from primitive_db.constants import (
    DEFAULT_ID_SCHEMA,
    ID_COLUMN,
    INT_TYPE,
    INVALID_VALUE_MESSAGE,
    PYTHON_TYPES,
    VALID_TYPES,
)
from primitive_db.decorators import confirm_action, handle_db_errors, log_time
from primitive_db.utils import valid_table_name


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Validate columns and add the table schema to metadata."""
    if table_name in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" уже существует.')
    if not valid_table_name(table_name):
        raise ValueError(INVALID_VALUE_MESSAGE.format(value=table_name))
    if not columns:
        raise ValueError(INVALID_VALUE_MESSAGE.format(value=columns))
    schema = [DEFAULT_ID_SCHEMA]
    names = set()
    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            raise ValueError(INVALID_VALUE_MESSAGE.format(value=column))
        name, data_type = parts
        if not name.isidentifier() or data_type not in VALID_TYPES:
            raise ValueError(INVALID_VALUE_MESSAGE.format(value=column))
        if name in names:
            raise ValueError(f'Ошибка: Столбец "{name}" указан несколько раз.')
        names.add(name)
        if name == ID_COLUMN:
            if data_type != INT_TYPE:
                raise ValueError(INVALID_VALUE_MESSAGE.format(value=column))
        else:
            schema.append(column)
    metadata[table_name] = schema
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Remove an existing schema after confirmation."""
    if table_name not in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" не существует.')
    del metadata[table_name]
    return metadata


@handle_db_errors
def get_schema(metadata, table_name):
    """Return the ordered column names and types of an existing table."""
    if table_name not in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" не существует.')
    return dict(column.split(":") for column in metadata[table_name])


@handle_db_errors
def validate_clause(metadata, table_name, clause):
    """Check field existence and exact Python value types."""
    schema = get_schema(metadata, table_name)
    if schema is None:
        return None
    for name, value in clause.items():
        if name not in schema:
            raise ValueError(
                f'Ошибка: Столбец "{name}" не существует в таблице "{table_name}".'
            )
        if type(value) is not PYTHON_TYPES[schema[name]]:
            raise ValueError(INVALID_VALUE_MESSAGE.format(value=repr(value)))
    return True


@handle_db_errors
@log_time
def insert(metadata, table_name, table_data, values):
    """Return all records plus a validated new record with an automatic ID."""
    schema = get_schema(metadata, table_name)
    if schema is None:
        return None
    columns = [name for name in schema if name != ID_COLUMN]
    if len(values) != len(columns):
        raise ValueError(INVALID_VALUE_MESSAGE.format(value=values))
    record = dict(zip(columns, values))
    if validate_clause(metadata, table_name, record) is None:
        return None
    new_id = max((row[ID_COLUMN] for row in table_data), default=0) + 1
    return [row.copy() for row in table_data] + [{ID_COLUMN: new_id, **record}]


def matches_where(row, where_clause):
    """Return whether a record satisfies the equality condition."""
    return where_clause is None or all(
        row.get(name) == value for name, value in where_clause.items()
    )


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Return copies of matching records; engine manages query caching."""
    return [row.copy() for row in table_data if matches_where(row, where_clause)]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Return a new full table without modifying the input records."""
    if ID_COLUMN in set_clause:
        raise ValueError("Ошибка: Изменение столбца ID запрещено.")
    return [
        {**row, **set_clause} if matches_where(row, where_clause) else row.copy()
        for row in table_data
    ]


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data, where_clause):
    """Return remaining records after confirmation, leaving input untouched."""
    return [row.copy() for row in table_data if not matches_where(row, where_clause)]
