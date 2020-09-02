from collections import UserDict
from datetime import date, datetime, time
from decimal import Decimal
from json import JSONEncoder, dumps, loads
from uuid import UUID

__all__ = ["BSEncoder", "dumps", "loads"]

"""
    - def: __init__
        :param: self
        :param: m
"""
class TranslationMap(UserDict):
    def __init__(self, m):
        super().__init__(m)

"""
    - def: default
        :param: self
        :param: obj
    - def: BSEncoder
        :param: locale
"""
class _BSEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return datetime.isoformat(obj)
        elif isinstance(obj, date):
            return date.isoformat(obj)
        elif isinstance(obj, time):
            return time.isoformat(obj)
        # Let the base class default method raise the TypeError
        return super().default(obj)

def BSEncoder(locale="en"):
    if locale == "pt-br":
        locale = "br"
    return type("BetEncoder_" + locale, (_BSEncoder,), {"locale": locale})
