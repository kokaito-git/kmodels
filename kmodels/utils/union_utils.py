from __future__ import annotations

import types
from typing import get_origin, Any, Union, get_args


class UnionUtils:
    @staticmethod
    def is_union_type(tp: Any) -> bool:
        """
        Retorna True si tp es un typing.Union o un types.UnionType (Python 3.10+).
        """
        return get_origin(tp) is Union or isinstance(tp, types.UnionType)

    @staticmethod
    def ensure_tuple(tp: Any) -> tuple[type, ...]:
        """
        Convierte un Union (typing.Union o types.UnionType) a una tupla de tipos individuales.
        - Si ya es una tupla entonces retornará la tupla.
        - Si es cualquier otra cosa entonces retornará (tp,)
        """
        if UnionUtils.is_union_type(tp):
            return get_args(tp)
        elif isinstance(tp, tuple):
            return tp
        else:
            return (tp,)
