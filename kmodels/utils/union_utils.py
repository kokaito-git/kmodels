from __future__ import annotations

import types
from typing import get_origin, Any, Union, get_args, Literal, Type, Iterable

from kmodels.utils.literal_utils import LiteralUtils


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

        [!] Por tanto, no convierte iterables en tuplas sino que los va a meter dentro de una tupla.
        """
        if UnionUtils.is_union_type(tp):
            return get_args(tp)
        elif isinstance(tp, tuple):
            return tp
        else:
            return (tp,)

    @classmethod
    def extract_types(cls, iterable: Iterable) -> tuple[type, ...]:
        """
        Crea una lista con los tipos únicos encontrados, ya sea en los elementos que son tipos, uniones, o los tipos
        encontrados dentro de los literales.

        En cuanto a los Union los despliega.
        En cuanto a los Literals extrae los tipos que encuentre.
        En cuanto a None lo ignora (no es un tipo).
        """
        extracted_types = []
        for item in iterable:
            if isinstance(item, type):
                extracted_types.append(item)
            elif UnionUtils.is_union_type(item):
                extracted_types.extend(cls.ensure_tuple(item))
            elif LiteralUtils.is_literal(item):
                args = get_args(item)
                literal_types = list(type(t) for t in args)
                extracted_types.extend(literal_types)
        return tuple(set(extracted_types))

    @classmethod
    def extract_non_types[T](cls, iterable: Iterable) -> tuple[Any, ...]:
        """Extrae todos los elementos que no son tipos, uniones o literales."""
        non_types = []
        for item in iterable:
            if not isinstance(item, type) and not UnionUtils.is_union_type(item) and not LiteralUtils.is_literal(item):
                non_types.append(item)
        return tuple(non_types)

    @classmethod
    def isinstance(cls, value: Any, tt: tuple[type | Union | Literal, ...]) -> bool:
        """Válida el tipo correctamente sin importar si es un tipo, una Union o un Literal."""
        if not isinstance(tt, tuple):
            raise TypeError(f"The 'valid_type' parameter must be a tuple, not {type(tt)}")

        # Validamos el tipo (ahí están los posibles tipos)
        all_types = cls.extract_types(tt)
        if not isinstance(value, tuple(all_types)):
            return False

        literals = [v for lit_types in tt if LiteralUtils.is_literal(lit_types) for v in get_args(lit_types)]
        if literals:
            return value in literals
        return True

    @classmethod
    def raise_not_isinstance(cls, value: Any, tt: tuple[type | Union | Literal, ...]) -> None:
        """Lanza un TypeError si el valor no es una instancia de los tipos especificados."""
        if not cls.isinstance(value, tt):
            # Obtenemos los tipos válidos
            # Validamos el tipo (ahí están los posibles tipos)
            valid_types = cls.extract_types(tt)

            if not isinstance(value, valid_types):
                valid_types_msg = ", ".join([f"{t.__name__}" for t in valid_types])
                raise TypeError(
                    f'Expected type(s): ({valid_types_msg}), but got [Type: "{type(value).__name__}", Value: {value}].'
                )

            literals = [v for lit_types in tt if LiteralUtils.is_literal(lit_types) for v in get_args(lit_types)]
            if literals:
                if value not in literals:
                    literals_msg = ", ".join([f"{v}" for v in literals])
                    raise TypeError(
                        f'Expected one of the following literals: [{literals_msg}], '
                        f'but got [Type: "{type(value).__name__}", Value: {value}].'
                    )


def test():
    # result = UnionUtils.isinstance('5', (Literal[1, 2, 3], Literal['5']))
    # print(result)

    UnionUtils.raise_not_isinstance(5, (Literal[1, 2, 3],))


if __name__ == '__main__':
    test()
