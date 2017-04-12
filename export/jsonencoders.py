import sys
import json
import abc
from typing import Any, Dict


class JSONable(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def to_json(self) -> Dict[str, str]:
        d = {"class": type(self).__name__, "module": type(self).__module__}
        return d

    @classmethod
    def from_json(cls, **kwargs) -> "JSONable":
        return cls(**kwargs)


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            return o.to_json()
        except AttributeError:
            return super().default(o)


def json_decoder(o):
    if "class" in o and "module" in o:
        try:
            m = o["module"]
            c = o["class"]
            cls = getattr(sys.modules[m], c)
        except AttributeError as a:
            print(a)
        else:
            del o["class"]
            del o["module"]
            try:
                return cls.from_json(**o)
            except AttributeError as a:
                print(a)
    return o


def load_string(s: str) -> Any:
    return json.loads(s, object_hook=json_decoder)


def dump_string(obj) -> str:
    return json.dumps(obj, cls=JSONEncoder)
