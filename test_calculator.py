import math
from io import StringIO

import pytest

from calculator import Calculator


class TestCalculator:
    """Обычные вычисления, ошибки ввода и предыдущий результат."""

    def setup_method(self):
        self.calc = Calculator()

    def test_numbers(self):
        assert self.calc.calculate("0") == 0.0
        assert self.calc.calculate("-2.5") == -2.5
        assert self.calc.calculate("1e-3 + .5") == pytest.approx(0.501)

    @pytest.mark.parametrize("expression, expected", [
        ("2 + 3", 5.0),
        ("5 - 3", 2.0),
        ("2 * 3", 6.0),
        ("7 / 2", 3.5),
        ("2 ^ 3", 8.0),
    ])
    def test_basic_operators(self, expression, expected):
        assert self.calc.calculate(expression) == expected

    def test_precedence_and_parentheses(self):
        assert self.calc.calculate("2 + 3 * 4") == 14.0
        assert self.calc.calculate("(2 + 3) * 4") == 20.0
        assert self.calc.calculate("2 * (3 + (4 - 1)^2)") == 24.0

    def test_operation_order(self):
        assert self.calc.calculate("20 - 5 - 3") == 12.0
        assert self.calc.calculate("8 / 4 / 2") == 1.0
        assert self.calc.calculate("2^3^2") == 512.0
        assert self.calc.calculate("(2^3)^2") == 64.0

    def test_unary_minus(self):
        assert self.calc.calculate("-2^2") == -4.0
        assert self.calc.calculate("(-2)^2") == 4.0
        assert self.calc.calculate("5 - -3") == 8.0
        assert self.calc.calculate("-(2 + 3)") == -5.0
        assert self.calc.calculate("2 *\t-3") == -6.0
        assert self.calc.calculate("2 ^ -3") == 0.125

    @pytest.mark.parametrize("expression", [
        "",             # Пустой ввод
        "2 @ 3",        # Посторонний символ
        "sin(0)",       # Неподдерживаемая функция
        "(2 + 3",       # Незакрытая скобка
        ")(2)",         # Лишняя закрывающая скобка
        "()",           # Пустые скобки
        "2 +",          # Нет второго операнда
        "2 3",          # Нет оператора
        "2(3)",         # Неявное умножение не поддерживается
        "- + -3",       # Унарный плюс не поддерживается
        "2+-3",         # Минус вплотную к другому оператору
    ])
    def test_invalid_expressions(self, expression):
        with pytest.raises(ValueError):
            self.calc.calculate(expression)

    def test_characters_are_checked_before_parentheses(self):
        with pytest.raises(ValueError, match="Недопустимый символ"):
            self.calc.calculate("2 + @(")

    def test_previous_result(self):
        assert self.calc.calculate("2 + 3") == 5.0
        assert self.calc.calculate("_ * 2") == 10.0
        assert self.calc.calculate("_ - 10") == 0.0
        assert self.calc.calculate("_ + 1") == 1.0

    def test_error_preserves_previous_result(self):
        self.calc.calculate("5")
        with pytest.raises(ValueError):
            self.calc.calculate("2 +")
        assert self.calc.calculate("_") == 5.0

    def test_previous_result_is_not_defined_at_start(self):
        with pytest.raises(ValueError):
            self.calc.calculate("_ + 1")


class TestSpecialValues:
    """Бесконечности и неопределённости."""

    def setup_method(self):
        self.calc = Calculator()

    def test_infinity(self):
        assert self.calc.calculate("+inf") == math.inf
        assert self.calc.calculate("-INF") == -math.inf
        assert self.calc.calculate("inf + 2") == math.inf
        assert self.calc.calculate("inf * -2") == -math.inf

    def test_division_by_zero(self):
        assert self.calc.calculate("1 / 0") == math.inf
        assert self.calc.calculate("1 / (-0)") == -math.inf
        assert self.calc.calculate("-1 / (-0)") == math.inf

    @pytest.mark.parametrize("expression", [
        "0 / 0",
        "inf / inf",
        "0 * inf",
        "inf - inf",
        "1 ^ inf",
        "inf ^ 0",
        "0 ^ 0",
    ])
    def test_seven_indeterminate_forms(self, expression):
        assert math.isnan(self.calc.calculate(expression))

    def test_nan_propagates(self):
        assert math.isnan(self.calc.calculate("nan + 1"))
        assert math.isnan(self.calc.calculate("(0/0)^0"))
        assert math.isnan(self.calc.calculate("1^nan"))
        assert math.isnan(self.calc.calculate("_ + 1"))

    def test_power_overflow(self):
        assert self.calc.calculate("10^1000") == math.inf
        assert self.calc.calculate("(-10)^1001") == -math.inf

    def test_special_powers(self):
        assert self.calc.calculate("2^0") == 1.0
        assert self.calc.calculate("inf^2") == math.inf
        assert self.calc.calculate("0 ^ -1") == math.inf
        assert self.calc.calculate("(-0) ^ -3") == -math.inf
        assert math.isnan(self.calc.calculate("(-2)^0.5"))


class TestInteractive:
    """Проверяем ввод и вывод как при работе в терминале."""

    def test_session_continues_after_error(self, monkeypatch, capsys):
        user_input = StringIO("2 + 3\n_ * 2\n2 +\n_ + 1\nquit\n")
        monkeypatch.setattr("sys.stdin", user_input)

        Calculator()()

        text = capsys.readouterr().out
        assert "exit или quit" in text
        assert "Введите выражение: 5.0\n" in text
        assert "Введите выражение: 10.0\n" in text
        assert "Ошибка: Не хватает операнда" in text
        assert "Введите выражение: 11.0\n" in text

    def test_negative_zero_is_hidden_only_in_output(self, monkeypatch, capsys):
        user_input = StringIO("-0\n1/_\n1/(-inf)\n-1e-300\nexit\n")
        monkeypatch.setattr("sys.stdin", user_input)

        Calculator()()

        text = capsys.readouterr().out
        assert "-0.0" not in text
        assert "Введите выражение: 0.0\n" in text
        assert "Введите выражение: -inf\n" in text
        assert "Введите выражение: -1e-300\n" in text
