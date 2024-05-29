from my_package.sublib import my_sublib  # type: ignore

from .sublib.my_sublib import MyClass

assert MyClass == my_sublib.MyClass
