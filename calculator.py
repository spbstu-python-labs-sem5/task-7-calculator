import math
import re


class Calculator:
    TOKEN_PATTERN = re.compile(
        r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
        r"|inf|nan|[+\-*/^()_]|\s+",
        re.IGNORECASE,
    )

    def __init__(self):
        self.previous_result = None
        self._tokens = iter(())
        self._current_token = None


    def check_characters(self, expression: str) -> None:
        """Проверяет, что строка содержит только допустимые числа и обозначения"""
        for part in self.TOKEN_PATTERN.split(expression):
            if part:
                raise ValueError(f"Недопустимый символ {part[0]!r}")


    def check_parentheses(self, expression: str) -> None:
        """Проверяет баланс и порядок открывающих и закрывающих скобок"""
        depth = 0

        for character in expression:
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth < 0:
                    raise ValueError("Найдена лишняя закрывающая скобка!")

        if depth > 0:
            raise ValueError("Найдены незакрытые скобки!")


    def parse_number(self, text: str) -> float | None:
        """Преобразует строку в число, если она целиком содержит число"""
        try:
            return float(text)
        except ValueError:
            return None


    def find_unary_minuses(self, expression: str) -> list[int]:
        """Определяет унарные минусы по предыдущему непробельному символу"""
        positions = []
        previous_character = None
        previous_index = None

        for index, character in enumerate(expression):
            if character.isspace():
                continue

            if character == "-":
                after_operator = previous_character in ("+", "-", "*", "/", "^")
                if after_operator and previous_index == index - 1:
                    raise ValueError(f"Унарный минус на позиции {index} нужно отделять пробелом от предыдущего оператора")
                if previous_character in (None, "(") or after_operator:
                    positions.append(index)

            previous_character = character
            previous_index = index

        return positions


    def split_parentheses(self, expression: str) -> list[str]:
        """Разделяет выражение по скобкам, сохраняя их отдельными элементами"""
        parts = re.split(r"([()])", expression)
        return [part.strip() for part in parts if part.strip()]


    def tokenize(self, expression: str) -> list[str]:
        """Разделяет выражение на токены, обозначая унарный минус как u-"""
        unary_minuses = set(self.find_unary_minuses(expression))
        tokens = []
        for match in self.TOKEN_PATTERN.finditer(expression):
            token = match.group()
            if token.isspace():
                continue
            if match.start() in unary_minuses:
                token = "u-"
            tokens.append(token)
        return tokens


    def _next_token(self) -> None:
        self._current_token = next(self._tokens, None)


    def _parse_expression(self) -> float:
        """Сложение и вычитание: операции с наименьшим приоритетом"""
        result = self._parse_term()
        while self._current_token in ("+", "-"):
            operator = self._current_token
            self._next_token()
            right = self._parse_term()
            result = result + right if operator == "+" else result - right
        return result


    def _parse_term(self) -> float:
        """Умножение и деление выполняются слева направо"""
        result = self._parse_unary()
        while self._current_token in ("*", "/"):
            operator = self._current_token
            self._next_token()
            right = self._parse_unary()
            if operator == "*":
                result *= right
            else:
                result = self._divide(result, right)
        return result


    def _divide(self, left: float, right: float) -> float:
        """При делении на ноль возвращает nan или бесконечность с нужным знаком"""
        if right == 0:
            if left == 0 or math.isnan(left):
                return math.nan
            sign = math.copysign(1.0, left) * math.copysign(1.0, right)
            return math.copysign(math.inf, sign)
        return left / right


    def _parse_unary(self) -> float:
        """Унарный минус применяется после возведения в степень"""
        if self._current_token == "u-":
            self._next_token()
            # здесь рекурсивно вызывается, чтобы обработать несколько унарных минусов подряд
            return -self._parse_unary()
        return self._parse_power()


    def _parse_power(self) -> float:
        """Степень разбирается справа налево: 2^3^2 = 2^(3^2)"""
        base = self._parse_atom()
        if self._current_token == "^":
            self._next_token()
            exponent = self._parse_unary()
            return self._power_with_undefined_cases(base, exponent)
        return base


    def _power_with_undefined_cases(self, base: float, exponent: float) -> float:
        """Обрабатывает переполнение и неопределённые результаты степени"""
        if math.isnan(base) or math.isnan(exponent):
            return math.nan
        if exponent == 0 and (base == 0 or math.isinf(base)):
            return math.nan
        if abs(base) == 1 and math.isinf(exponent):
            return math.nan

        negative_odd_power = (
            math.copysign(1.0, base) < 0
            and math.isfinite(exponent)
            and exponent.is_integer()
            and exponent % 2 != 0
        )
        infinity = -math.inf if negative_odd_power else math.inf

        try:
            return math.pow(base, exponent)
        except OverflowError:
            return infinity
        except ValueError:
            if base == 0 and exponent < 0:
                return infinity
            return math.nan


    def _parse_atom(self) -> float:
        """Число, предыдущий результат или выражение в скобках"""
        token = self._current_token
        if token is None:
            raise ValueError("Не хватает операнда")

        if token == "(":
            self._next_token()
            result = self._parse_expression()
            if self._current_token != ")":
                raise ValueError("Ожидалась закрывающая скобка")
            self._next_token()
            return result

        if token == "_":
            if self.previous_result is None:
                raise ValueError("Предыдущий результат ещё не определён")
            self._next_token()
            return self.previous_result

        if token == "+":
            self._next_token()
            token = self._current_token
            if token is None or token.lower() != "inf":
                raise ValueError("Унарный плюс допустим только перед inf")

        number = self.parse_number(token)
        if number is None:
            raise ValueError(f"Ожидалось число или '(', получено {token!r}")
        self._next_token()
        return number


    def calculate(self, expression: str) -> float:
        """Проверяет выражение, вычисляет его и сохраняет результат"""
        self.check_characters(expression)
        self.check_parentheses(expression)
        if not expression.strip():
            raise ValueError("пустое выражение")

        # создаем итератор, возвращающий спраршенные части
        self._tokens = iter(self.tokenize(expression))
        # после создания итератора получаем перый эл-т
        self._next_token()

        result = self._parse_expression()
        # между числами не нашелся оператор
        if self._current_token is not None:
            raise ValueError(f"Ожидался оператор перед {self._current_token!r}")

        self.previous_result = result
        return result


    def __call__(self) -> None:
        print("Для выхода введите exit или quit. Можно также нажать Ctrl+C или Ctrl+D.")
        
        while True:
            try:
                expression = input("Введите выражение: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if expression.lower() in ("exit", "quit"):
                break

            try:
                result = self.calculate(expression)
                print(0.0 if result == 0 else result)
            except ValueError as error:
                print(f"Ошибка: {error}")


if __name__ == "__main__":
    Calculator()()
