import json
import shlex

from primitive_db.constants import (
    ASSIGNMENT_TOKEN_COUNT,
    COMMAND_PUNCTUATION,
    INSERT_VALUES_START,
    INVALID_VALUE_MESSAGE,
    MIN_INSERT_ARGUMENTS,
    MIN_QUERY_ARGUMENTS,
    MIN_UPDATE_ARGUMENTS,
    QUERY_CONDITION_START,
    QUERY_WHERE_INDEX,
    SET_ASSIGNMENT_STRIDE,
    SET_CLAUSE_START,
    UPDATE_WHERE_START,
)


def invalid_value(value):
    """Return the assignment's standard invalid-input exception."""
    if isinstance(value, list):
        value = " ".join(value)
    return ValueError(INVALID_VALUE_MESSAGE.format(value=value))


def tokenize(expression):
    """Split commands while retaining quoted text and punctuation."""
    lexer = shlex.shlex(expression, posix=False, punctuation_chars=COMMAND_PUNCTUATION)
    lexer.whitespace_split = True
    lexer.commenters = ""
    tokens = []
    try:
        for token in lexer:
            if all(character in COMMAND_PUNCTUATION for character in token):
                tokens.extend(token)
            else:
                tokens.append(token)
    except ValueError as error:
        raise invalid_value(expression) from error
    return tokens


def parse_value(token):
    """Parse a quoted string, integer, or case-insensitive boolean literal."""
    if token.startswith(('"', "'")):
        try:
            if token.startswith('"'):
                value = json.loads(token)
            else:
                pieces = shlex.split(token)
                if len(pieces) != 1:
                    raise invalid_value(token)
                value = pieces[0]
        except ValueError as error:
            raise invalid_value(token) from error
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
    raise invalid_value(token)


def parse_where_clause(expression):
    """Convert one equality into a column-to-value dictionary."""
    tokens = tokenize(expression) if isinstance(expression, str) else expression
    if (
        len(tokens) != ASSIGNMENT_TOKEN_COUNT
        or not tokens[0].isidentifier()
        or tokens[1] != "="
    ):
        raise invalid_value(tokens)
    return {tokens[0]: parse_value(tokens[2])}


def parse_set_clause(expression):
    """Parse assignments separated by commas, rejecting duplicate fields."""
    tokens = tokenize(expression) if isinstance(expression, str) else expression
    if not tokens:
        raise invalid_value(tokens)
    result = {}
    position = 0
    while position < len(tokens):
        clause = parse_where_clause(
            tokens[position : position + ASSIGNMENT_TOKEN_COUNT]
        )
        name = next(iter(clause))
        if name in result:
            raise invalid_value(tokens)
        result.update(clause)
        position += ASSIGNMENT_TOKEN_COUNT
        if position == len(tokens):
            break
        if tokens[position] != "," or position + 1 == len(tokens):
            raise invalid_value(tokens)
        position += 1
    return result


def parse_values(tokens):
    """Parse exactly one parenthesized list of comma-separated values."""
    if len(tokens) < 2 or tokens[0] != "(" or tokens[-1] != ")":
        raise invalid_value(tokens)
    items = tokens[1:-1]
    if not items:
        return []
    if len(items) % 2 == 0 or any(token != "," for token in items[1::2]):
        raise invalid_value(tokens)
    return [parse_value(token) for token in items[::2]]


def parse_insert_command(arguments):
    """Require one table name and one values group after into."""
    if (
        len(arguments) < MIN_INSERT_ARGUMENTS
        or arguments[0] != "into"
        or arguments[2] != "values"
    ):
        raise invalid_value(arguments)
    return arguments[1], parse_values(arguments[INSERT_VALUES_START:])


def parse_query_command(arguments, allow_without_where=False):
    """Parse from <table> with an optional equality for select only."""
    if len(arguments) < MIN_QUERY_ARGUMENTS or arguments[0] != "from":
        raise invalid_value(arguments)
    if len(arguments) == MIN_QUERY_ARGUMENTS and allow_without_where:
        return arguments[1], None
    if len(arguments) <= QUERY_WHERE_INDEX or arguments[QUERY_WHERE_INDEX] != "where":
        raise invalid_value(arguments)
    return arguments[1], parse_where_clause(arguments[QUERY_CONDITION_START:])


def parse_update_command(arguments):
    """Parse a table, set assignments, and exactly one where condition."""
    if len(arguments) < MIN_UPDATE_ARGUMENTS or arguments[1] != "set":
        raise invalid_value(arguments)
    where_position = next(
        (
            index
            for index in range(
                UPDATE_WHERE_START, len(arguments), SET_ASSIGNMENT_STRIDE
            )
            if arguments[index] == "where"
        ),
        None,
    )
    if where_position is None:
        raise invalid_value(arguments)
    return (
        arguments[0],
        parse_set_clause(arguments[SET_CLAUSE_START:where_position]),
        parse_where_clause(arguments[where_position + 1 :]),
    )
