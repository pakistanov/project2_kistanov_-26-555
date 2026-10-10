import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from primitive_db.core import create_table, drop_table
from primitive_db.utils import load_metadata, save_metadata


class TableTests(unittest.TestCase):
    def test_create_and_drop(self):
        metadata = {}
        with contextlib.redirect_stdout(io.StringIO()):
            result = create_table(
                metadata, "users", ["name:str", "age:int", "active:bool"]
            )
        self.assertIs(result, metadata)
        self.assertEqual(
            metadata["users"], ["ID:int", "name:str", "age:int", "active:bool"]
        )
        with contextlib.redirect_stdout(io.StringIO()):
            drop_table(metadata, "users")
        self.assertEqual(metadata, {})

    def test_explicit_id_is_first_and_not_duplicated(self):
        metadata = {}
        with contextlib.redirect_stdout(io.StringIO()):
            create_table(metadata, "users", ["name:str", "ID:int"])
        self.assertEqual(metadata["users"], ["ID:int", "name:str"])

    def test_invalid_columns_do_not_partially_create_table(self):
        for columns in (
            ["valid:str", "bad:float"],
            ["valid:str", "missing_type"],
            ["name:str", "name:int"],
            ["ID:str"],
            ["ID:int", "id:int"],
            ["bad-name:str"],
            ["name:str:extra"],
            [],
        ):
            with self.subTest(columns=columns):
                metadata = {"existing": ["ID:int"]}
                with contextlib.redirect_stdout(io.StringIO()):
                    create_table(metadata, "new_table", columns)
                self.assertEqual(metadata, {"existing": ["ID:int"]})

    def test_duplicate_table_and_missing_drop_leave_data_unchanged(self):
        metadata = {"users": ["ID:int", "name:str"]}
        with contextlib.redirect_stdout(io.StringIO()):
            create_table(metadata, "users", ["age:int"])
            drop_table(metadata, "missing")
            create_table(metadata, "bad-name", ["name:str"])
        self.assertEqual(metadata, {"users": ["ID:int", "name:str"]})

    def test_metadata_round_trip_and_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "db_meta.json"
            self.assertEqual(load_metadata(path), {})
            data = {"товары": ["ID:int", "название:str"]}
            save_metadata(path, data)
            self.assertEqual(load_metadata(path), data)
            self.assertFalse(path.with_name("db_meta.json.tmp").exists())


class CommandTests(unittest.TestCase):
    def run_commands(self, directory, commands):
        environment = dict(os.environ, PYTHONIOENCODING="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "primitive_db.main"],
            input=commands,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=directory,
            env=environment,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout

    def test_tables_persist_across_restarts(self):
        with tempfile.TemporaryDirectory() as directory:
            output = self.run_commands(
                directory, "create_table users name:str age:int active:bool\nexit\n"
            )
            self.assertIn('Таблица "users" успешно создана', output)
            output = self.run_commands(directory, "list_tables\nexit\n")
            self.assertIn("- users", output)
            output = self.run_commands(directory, "drop_table users\nexit\n")
            self.assertIn('Таблица "users" успешно удалена', output)
            self.assertEqual(load_metadata(Path(directory) / "db_meta.json"), {})

    def test_invalid_commands_help_quotes_and_eof(self):
        with tempfile.TemporaryDirectory() as directory:
            output = self.run_commands(
                directory,
                "\nunknown\ncreate_table\ndrop_table\nlist_tables extra\n"
                'exit extra\ncreate_table "broken\nhelp\n'
                'create_table "users" "name:str"\nexit\n',
            )
            self.assertIn("Функции unknown нет. Попробуйте снова.", output)
            self.assertIn("Некорректное значение:", output)
            self.assertGreaterEqual(output.count("***Процесс работы с таблицей***"), 2)
            self.assertEqual(
                load_metadata(Path(directory) / "db_meta.json"),
                {"users": ["ID:int", "name:str"]},
            )
            self.assertIn("Выход из программы.", self.run_commands(directory, ""))

    def test_corrupt_metadata_is_not_overwritten(self):
        for content in ("{broken", "[]", '{"users": 42}'):
            with (
                self.subTest(content=content),
                tempfile.TemporaryDirectory() as directory,
            ):
                path = Path(directory) / "db_meta.json"
                path.write_text(content, encoding="utf-8")
                output = self.run_commands(directory, "create_table users name:str\n")
                self.assertIn("Ошибка загрузки метаданных:", output)
                self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_rejected_operations_do_not_write_file(self):
        with tempfile.TemporaryDirectory() as directory:
            self.run_commands(
                directory, "create_table users name:float\ndrop_table missing\nexit\n"
            )
            self.assertFalse((Path(directory) / "db_meta.json").exists())


if __name__ == "__main__":
    unittest.main()
