import re


def parse_number(text: str) -> float | None:
    """Преобразует строку в число, если она целиком содержит число"""
    try:
        return float(text)
    except ValueError:
        return None


def find_unary_minuses(expression: str) -> list[int]:
    """Находит минусы в начале выражения или после открывающей скобки"""
    positions = []
    previous = None

    for index, character in enumerate(expression):
        if character.isspace():
            continue
        if character == "-" and previous in (None, "("):
            positions.append(index)
        previous = character

    return positions


def split_parentheses(expression: str) -> list[str]:
    """Разделяет выражение по скобкам, сохраняя их отдельными элементами."""
    parts = re.split(r"([()])", expression)
    return [part.strip() for part in parts if part.strip()]


def main() -> None:
    expression = input("Введите число или выражение: ").strip()
    if not expression:
        print("Ошибка: пустое выражение")
        return

    number = parse_number(expression)
    if number is not None:
        print(number)
        return

    unary_minuses = find_unary_minuses(expression)
    parts = split_parentheses(expression)
    print("Позиции унарных минусов (с нуля):", unary_minuses)
    print("Части выражения:", parts)


if __name__ == "__main__":
    main()
