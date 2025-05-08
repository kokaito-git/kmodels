from typing import Union, TypeVar, overload, Type, Generic, Iterable
import typeguard
from kmodels.types import Unset

_T = TypeVar('_T')

# Tipos de salida soportados
_ITER_OBJ = Union[list[_T], tuple[_T, ...], set[_T], Unset, None]
_ITER_OBJ_T = Type[_ITER_OBJ]


class IterableUtils(Generic[_T]):
    def __init__(self, element_t: Type[_T], type_validation: bool = True):
        self._element_t = element_t
        self._type_validation = type_validation

    @overload
    def ensure_iterable(
            self,
            iterable: Iterable[_T] | _T,
            output_t: Type[list[_T]],
    ) -> list[_T]:
        ...

    @overload
    def ensure_iterable(
            self,
            iterable: Iterable[_T] | _T,
            output_t: Type[tuple[_T, ...]],
    ) -> tuple[_T, ...]:
        ...

    @overload
    def ensure_iterable(
            self,
            iterable: Iterable[_T] | _T,
            output_t: Type[set[_T]],
    ) -> set[_T]:
        ...

    def ensure_iterable(
            self,
            iterable: Iterable[_T] | _T,
            output_t: _ITER_OBJ_T[_T],
    ) -> _ITER_OBJ[_T]:
        # Manejo de None o Unset
        if iterable is None or isinstance(iterable, Unset):
            result = output_t()

        # Sí es un solo elemento del tipo esperado
        elif isinstance(iterable, self._element_t):
            result = output_t((iterable,))

        # Si es un iterable (incluye tuple y set)
        elif isinstance(iterable, Iterable):
            result = output_t(iterable)
        else:
            raise TypeError(f"Expected iterable, tuple, or {self._element_t}, got {type(iterable)}")

        if self._type_validation:
            try:
                typeguard.check_type(result, output_t[self._element_t])
            except typeguard.TypeCheckError as e:
                raise TypeError(f'{e}.') from None

        return result


def custom_iterable_utils_builder(output_type: Type[_T], *, check_type: bool = True) -> IterableUtils[_T]:
    class CustomIterable(IterableUtils):
        def __init__(self):
            super().__init__(output_type, type_validation=check_type)

    return CustomIterable()


def test():
    utils_int = custom_iterable_utils_builder(int, check_type=True)
    result_int = utils_int.ensure_iterable(iterable='10', output_t=list)

    utils_str = custom_iterable_utils_builder(str)
    result_str = utils_str.ensure_iterable(iterable='10', output_t=tuple)


if __name__ == "__main__":
    test()
