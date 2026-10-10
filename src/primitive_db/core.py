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
