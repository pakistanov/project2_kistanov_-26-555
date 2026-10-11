from primitive_db.utils import load_table_data

SUPPORTED_TYPES = {"int", "str", "bool"}


def create_table(metadata, table_name, columns):
    """Validate a table schema and add it to the metadata."""
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata
    if not table_name.isidentifier():
        print(f"Некорректное значение: {table_name}. Попробуйте снова.")
        return metadata
    if not columns:
        print("Ошибка: Укажите хотя бы один столбец в формате имя:тип.")
        return metadata

    schema = ["ID:int"]
    names = set()
    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata
        name, data_type = parts
        if not name.isidentifier() or data_type not in SUPPORTED_TYPES:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata
        normalized_name = "ID" if name.upper() == "ID" else name
        if normalized_name in names:
            print(f'Ошибка: Столбец "{normalized_name}" указан несколько раз.')
            return metadata
        names.add(normalized_name)
        if normalized_name == "ID":
            if data_type != "int":
                print(f"Некорректное значение: {column}. Попробуйте снова.")
                return metadata
        else:
            schema.append(column)

    metadata[table_name] = schema
    print(f'Таблица "{table_name}" успешно создана со столбцами: ' + ", ".join(schema))
    return metadata


def drop_table(metadata, table_name):
    """Remove an existing table from the metadata."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata
    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def get_schema(metadata, table_name):
    """Return column names and types for an existing table."""
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')
    return dict(column.split(":") for column in metadata[table_name])


def validate_clause(metadata, table_name, clause):
    """Validate column names and exact Python types against the schema."""
    schema = get_schema(metadata, table_name)
    python_types = {"int": int, "str": str, "bool": bool}
    for name, value in clause.items():
        if name not in schema:
            raise ValueError(f'Столбец "{name}" не существует.')
        if type(value) is not python_types[schema[name]]:
            raise ValueError(
                f'Столбец "{name}" требует тип {schema[name]}, '
                f"получено значение {value!r}."
            )


def insert(metadata, table_name, values):
    """Validate values and append a record with an automatically generated ID."""
    schema = get_schema(metadata, table_name)
    columns = [name for name in schema if name != "ID"]
    if len(values) != len(columns):
        raise ValueError(
            f"Ожидается {len(columns)} значений без ID, получено {len(values)}."
        )
    record = dict(zip(columns, values))
    validate_clause(metadata, table_name, record)
    data = load_table_data(table_name)
    new_id = max((row["ID"] for row in data), default=0) + 1
    data.append({"ID": new_id, **record})
    return data


def select(table_data, where_clause=None):
    """Return all rows or rows matching every equality in the condition."""
    if where_clause is None:
        return list(table_data)
    return [
        row
        for row in table_data
        if all(row.get(name) == value for name, value in where_clause.items())
    ]


def update(table_data, set_clause, where_clause):
    """Update matching records and return the changed table data."""
    matching_rows = select(table_data, where_clause)
    if "ID" in set_clause and matching_rows:
        new_id = set_clause["ID"]
        other_ids = [row["ID"] for row in table_data if row not in matching_rows]
        if new_id < 1 or len(matching_rows) > 1 or new_id in other_ids:
            raise ValueError("ID должен быть положительным и уникальным.")
    for row in matching_rows:
        row.update(set_clause)
    return table_data


def delete(table_data, where_clause):
    """Remove matching records and return the remaining rows."""
    return [
        row
        for row in table_data
        if not all(row.get(name) == value for name, value in where_clause.items())
    ]
