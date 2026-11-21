import re


class Calculator:
    TOKEN_PATTERN = re.compile(
        r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
        r"|inf|nan|[+\-*/^()_]|\s+",
        re.IGNORECASE,
    )

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


    def __call__(self) -> None:
        expression = input("Введите выражение: ").strip()

        try:
            self.check_characters(expression)
            self.check_parentheses(expression)
        except ValueError as error:
            print(f"Ошибка: {error}")
            return

        if not expression:
            print("Ошибка: пустое выражение")
            return

        number = self.parse_number(expression)
        if number is not None:
            print(number)
            return

        try:
            unary_minuses = self.find_unary_minuses(expression)
        except ValueError as error:
            print(f"Ошибка: {error}")
            return
        parts = self.split_parentheses(expression)
        print("Позиции унарных минусов (с нуля):", unary_minuses)
        print("Части выражения:", parts)


if __name__ == "__main__":
    Calculator()()
