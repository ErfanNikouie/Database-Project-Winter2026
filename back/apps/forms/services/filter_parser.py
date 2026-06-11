from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import and_, or_

from apps.common.exceptions import ValidationException


TOKEN_PATTERN = re.compile(r"\s*(\(|\)|\&|\||!=|>=|<=|=|>|<|[^\s\&\|\(\)]+)")


@dataclass
class TokenStream:
    tokens: list[str]
    index: int = 0

    def peek(self) -> str | None:
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def pop(self) -> str:
        token = self.peek()
        if token is None:
            raise ValidationException("Unexpected end of filter")
        self.index += 1
        return token


class FilterParser:
    @classmethod
    def parse(cls, field_name: str, field_type: str, expression: str, column):
        if expression is None or str(expression).strip() == "":
            return None

        if field_type in {"String", "Text", "Lookup"}:
            return cls._parse_string_like(field_name, expression, column)
        if field_type == "ForeignKey":
            normalized = expression.replace(",", "|")
            return cls._parse_logical_comparison(field_name, "Integer", normalized, column)
        if field_type == "Boolean":
            return cls._parse_bool(field_name, expression, column)
        return cls._parse_logical_comparison(field_name, field_type, expression, column)

    @classmethod
    def _parse_string_like(cls, field_name: str, expression: str, column):
        normalized = expression.replace(",", "|")
        values = [v.strip().strip('"').strip("'") for v in normalized.split("|") if v.strip()]
        if not values:
            return None

        include_values: list[str] = []
        exclude_values: list[str] = []
        for value in values:
            if value.startswith("!="):
                exclude_values.append(value[2:].strip())
            else:
                include_values.append(value)

        predicates = []
        if include_values:
            predicates.append(column.in_(include_values))
        if exclude_values:
            predicates.append(~column.in_(exclude_values))
        return and_(*predicates) if len(predicates) > 1 else predicates[0]

    @classmethod
    def _parse_bool(cls, field_name: str, expression: str, column):
        value = expression.strip().lower()
        if value == "empty":
            return None
        if value == "true":
            return column.is_(True)
        if value == "false":
            return column.is_(False)
        raise ValidationException("Invalid boolean filter", field=field_name)

    @classmethod
    def _parse_logical_comparison(cls, field_name: str, field_type: str, expression: str, column):
        tokens = [t for t in TOKEN_PATTERN.findall(expression) if t.strip()]
        stream = TokenStream(tokens=tokens)

        def parse_or_expr():
            left = parse_and_expr()
            while stream.peek() == "|":
                stream.pop()
                right = parse_and_expr()
                left = or_(left, right)
            return left

        def parse_and_expr():
            left = parse_factor()
            while stream.peek() == "&":
                stream.pop()
                right = parse_factor()
                left = and_(left, right)
            return left

        def parse_factor():
            token = stream.peek()
            if token == "(":
                stream.pop()
                inner = parse_or_expr()
                if stream.pop() != ")":
                    raise ValidationException("Missing closing parenthesis", field=field_name)
                return inner
            return parse_comparison()

        def parse_comparison():
            token = stream.pop()
            operators = {"!=", ">=", "<=", "=", ">", "<"}
            if token in operators:
                operator = token
                value_token = stream.pop()
            else:
                operator = "="
                value_token = token
            value = cls._cast_value(field_name, field_type, value_token)
            if operator == "=":
                return column == value
            if operator == "!=":
                return column != value
            if operator == ">":
                return column > value
            if operator == "<":
                return column < value
            if operator == ">=":
                return column >= value
            return column <= value

        parsed = parse_or_expr()
        if stream.peek() is not None:
            raise ValidationException("Invalid filter syntax", field=field_name)
        return parsed

    @staticmethod
    def _cast_value(field_name: str, field_type: str, raw_value: str):
        value = raw_value.strip().strip('"').strip("'")
        try:
            if field_type == "Integer":
                return int(value)
            if field_type == "Double":
                return float(value)
            if field_type == "Decimal":
                return Decimal(value)
            if field_type == "Date":
                return date.fromisoformat(value)
            if field_type == "DateTime":
                return datetime.fromisoformat(value)
            return value
        except (ValueError, TypeError):
            raise ValidationException("Invalid filter syntax", field=field_name) from None

