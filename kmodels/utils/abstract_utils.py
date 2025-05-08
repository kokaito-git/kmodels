from __future__ import annotations

import inspect
from abc import ABC
from typing import Type
from kmodels.error import IsAbstract


# Utilidad para manejar clases abstractas
class AbstractUtils:
    @classmethod
    def is_abstract(cls, target_class: Type):
        return inspect.isabstract(target_class) or ABC in target_class.__bases__

    @classmethod
    def raise_abstract_class(cls, target_class: Type):
        if cls.is_abstract(target_class):
            cname = target_class.__name__
            raise IsAbstract(f"{cname} is an abstract class (inherits from ABC) and you cannot instantiate it.")
