import datetime
from app.telegram.text_parser import TextInputParser, DateParser
from app.database.models import SearchInput


def test_search_input_parser():
    test_parser = TextInputParser(SearchInput)
    start_date = datetime.datetime.now().date() + datetime.timedelta(days=90)
    end_date = start_date + datetime.timedelta(days=5)

    output = SearchInput(location='grand canyon', start_date=start_date,
                         end_date=end_date)

    for strf in DateParser.allowed_date_formats.values():
        _group = tuple([output.location, output.start_date.strftime(strf), output.end_date.strftime(strf)])
        _string = ' '.join(_group)
        _parsed_group = tuple(test_parser.apply_regex(_string).values())
        _parsed_object = test_parser.parse(_string)
        assert _parsed_group == _group, f'{_parsed_group} is not equal to {_group}'
        assert _parsed_object == output, f'{_parsed_object} is not equal to {output}'
    try:
        test_parser.parse(_string[:-5])
    except ValueError:  # it is supposed to raise value error
        pass
