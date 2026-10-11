import time


def preserve_function_metadata(wrapper, func):
    """Keep function names and documentation without extra library imports."""
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__wrapped__ = func
    return wrapper


def handle_db_errors(func):
    """Report database errors and return None when an operation fails."""

    def wrapper(*args, **kwargs):
        """Run the decorated function with the additional behavior."""
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден. Возможно, база не инициализирована.")
        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")
        except ValueError as error:
            print(error)
        except Exception as error:
            print(f"Произошла непредвиденная ошибка: {error}")
        return None

    return preserve_function_metadata(wrapper, func)


def confirm_action(action_name):
    """Ask for confirmation before executing a destructive operation."""

    def decorator(func):
        """Add a confirmation prompt to the function."""

        def wrapper(*args, **kwargs):
            """Run the decorated function with the additional behavior."""
            try:
                answer = input(
                    f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
                )
            except (EOFError, KeyboardInterrupt):
                print("\nОперация отменена.")
                return None
            if answer.strip() != "y":
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)

        return preserve_function_metadata(wrapper, func)

    return decorator


def log_time(func):
    """Print the execution time while preserving the function's result."""

    def wrapper(*args, **kwargs):
        """Run the decorated function with the additional behavior."""
        started = time.monotonic()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.monotonic() - started
            print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд")

    return preserve_function_metadata(wrapper, func)


def create_cacher():
    """Return a function whose closure stores results by key."""
    cache = {}

    def cache_result(key, value_func):
        """Reuse a stored result or compute it once for a new key."""
        if key not in cache:
            value = value_func()
            if value is None:
                return None
            cache[key] = value
        return cache[key]

    return cache_result
