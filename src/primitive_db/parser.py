import json
import shlex

from primitive_db.constants import ASSIGNMENT_TOKEN_COUNT, COMMAND_PUNCTUATION


def tokenize(expression):
    """Split commands, retaining quoted strings and separating punctuation."""
    lexer = shlex.shlex(expression, posix=False, punctuation_chars=COMMAND_PUNCTUATION)
    lexer.whitespace_split = True
    lexer.commenters = ""
    tokens = []
    for token in lexer:
        if all(character in COMMAND_PUNCTUATION for character in token):
            tokens.extend(token)
        else:
            tokens.append(token)
    return tokens


def parse_value(token):
    """Parse a quoted string, integer, or true/false literal."""
    if token.startswith(('"', "'")):
        try:
            if token.startswith('"'):
                value = json.loads(token)
            else:
                pieces = shlex.split(token)
                if len(pieces) != 1:
                    raise ValueError("Ожидается одна строка в кавычках.")
                value = pieces[0]
        except ValueError as error:
            raise ValueError(f"Некорректная строка: {token}.") from error
        if isinstance(value, str):
            return value
    if token.lower() in {"true", "false"}:
        return token.lower() == "true"
    digits = token.lstrip("+-")
    if digits and digits.isascii() and digits.isdigit():
        try:
            return int(token)
        except ValueError:
            pass
    raise ValueError(
        f"Некорректное значение: {token}. "
        "Используйте целые числа, true/false или строки в кавычках."
    )


def parse_where_clause(expression):
    """Convert an equality such as age = 28 into a dictionary."""
    tokens = tokenize(expression) if isinstance(expression, str) else expression
    if (
        len(tokens) != ASSIGNMENT_TOKEN_COUNT
        or not tokens[0].isidentifier()
        or tokens[1] != "="
    ):
        raise ValueError("Условие должно иметь вид: <столбец> = <значение>.")
    return {tokens[0]: parse_value(tokens[2])}


def parse_set_clause(expression):
    """Parse one or more assignments separated by commas."""
    tokens = tokenize(expression) if isinstance(expression, str) else expression
    if not tokens:
        raise ValueError("Укажите присваивание после set.")
    result = {}
    position = 0
    while position < len(tokens):
        clause = parse_where_clause(
            tokens[position : position + ASSIGNMENT_TOKEN_COUNT]
        )
        name = next(iter(clause))
        if name in result:
            raise ValueError(f'Столбец "{name}" указан несколько раз.')
        result.update(clause)
        position += ASSIGNMENT_TOKEN_COUNT
        if position == len(tokens):
            break
        if tokens[position] != "," or position + 1 == len(tokens):
            raise ValueError("Разделяйте присваивания запятыми.")
        position += 1
    return result


def parse_values(tokens):
    """Parse the parenthesized list used by an insert command."""
    if len(tokens) < 2 or tokens[0] != "(" or tokens[-1] != ")":
        raise ValueError("Значения должны быть заключены в скобки: (значение, ...).")
    items = tokens[1:-1]
    if not items:
        return []
    if len(items) % 2 == 0 or any(token != "," for token in items[1::2]):
        raise ValueError("Разделяйте значения запятыми.")
    return [parse_value(token) for token in items[::2]]
