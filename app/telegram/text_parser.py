import datetime
from typing import Type
import re

from sqlmodel import SQLModel


class StrParser:

    @classmethod
    def parse(cls, string: str) -> str:
        return string

    @classmethod
    def regex(cls):
        return r'(.+)'


class DateParser:
    allowed_date_formats = {'yyyy/mm/dd': '%Y/%m/%d', 'mm/dd': '%m/%d'}

    @classmethod
    def parse(cls, string: str) -> datetime.date:
        date = None
        for date_format in cls.allowed_date_formats.values():
            try:
                date = datetime.datetime.strptime(string, date_format)
            except ValueError:
                pass
        assert date, ValueError(f'{string} is not a valid format for the date')
        now = datetime.datetime.now().date()
        if date.year == 1900:  # if missing year, assumes next coming (not fixed for leap years)
            date = datetime.date(now.year, date.month, date.day)
            if now > date:
                date = datetime.date(date.year + 1, date.month, date.day)
        return date

    @classmethod
    def regex(cls):
        return r'((?:\d{4}/|)\d{2}/\d{2})'


def get_parser(field_type: Type):
    if field_type == str:
        return StrParser
    if field_type == datetime.date:
        return DateParser


class TextInputParser:
    def __init__(self, output_type: Type[SQLModel]):
        self.output_type = output_type
        self.fields = {key: value.type_ for key, value in output_type.__fields__.items()}
        self.parsers = {key: get_parser(field_type=field_type) for key, field_type in self.fields.items()}

    def apply_regex(self, text: str):
        regex = r'^' + ' '.join(parser.regex() for parser in self.parsers.values()) + '$'
        p = re.compile(regex)
        match = re.match(p, text)
        if not (match and len(match.groups()) == len(self.parsers)):
            raise ValueError('Input does not match the pattern')
        groups = dict(zip(self.parsers.keys(), match.groups()))
        return groups

    def parse(self, text: str):
        groups = self.apply_regex(text=text)
        kwargs = {key: self.parsers[key].parse(group) for key, group in groups.items()}
        return self.output_type(**kwargs)
