import warnings
from typing import TypeVar, TYPE_CHECKING, Annotated, Any
from typing import final, Literal

from pydantic import BaseModel, ConfigDict

from kmodels.utils import UnionUtils

__all__ = ['OmitIfNone', 'OmitIfUnset', 'OmitIfValue', 'OmitIfType', 'Unset', 'Leave', 'unset', 'leave']

AnyType = TypeVar("AnyType")

if TYPE_CHECKING:
    OmitIfNone = Annotated[AnyType, ...]
    OmitIfUnset = Annotated[AnyType, ...]
    OmitIf = Annotated[Any, ...]
else:
    class OmitIfNone:
        def __class_getitem__(cls, item: Any) -> Any:
            """Clase utilizada para omitir la serialización de un campo si su valor es None."""
            return Annotated[item, OmitIfNone()]


    class OmitIfUnset:
        """Clase utilizada para omitir la serialización de un campo si su valor es Unset."""

        def __class_getitem__(cls, item: Any) -> Any:
            return Annotated[item, OmitIfUnset()]


    class OmitIfValue:
        """
        Clase utilizada para omitir la serialización de un campo si su valor es uno de los valores especificados.
        Para validar objetos str también funciona, pero el IDE se queja de que es un tipo por lo que puedes usar
        OmitIfTypes con Literal['cadena_valida'].
        """

        def __init__(self, excluded: Any):
            self.excluded = UnionUtils.ensure_tuple(excluded)

        @classmethod
        def __class_getitem__(cls, item: Any) -> Any:
            if not isinstance(item, tuple) or len(item) != 2:
                raise TypeError("OmitIfValue expects two arguments: OmitIfValue[FieldType, ExcludedValues]")
            field_type, excluded_values = item
            return Annotated[field_type, OmitIfValue(excluded_values)]


    class OmitIfType:
        """
        Clase utilizada para omitir la serialización de un campo si su valor es de los tipos especificados.
        Puedes usar tipos literales para validar str perfectamente.
        """

        def __init__(self, accepted: Any, excluded: Any):
            self.accepted = UnionUtils.ensure_tuple(accepted)
            self.excluded = UnionUtils.ensure_tuple(excluded)

        @classmethod
        def __class_getitem__(cls, item: tuple[Any, Any]) -> Any:
            if not isinstance(item, tuple) or len(item) != 2:
                raise TypeError("OmitIfType expects two arguments: OmitIfTypes[AcceptedType, ExcludedType]")
            accepted, excluded = item

            return Annotated[accepted, OmitIfType(accepted, excluded)]


    class OmitIf(OmitIfType):
        @classmethod
        def __class_getitem__(cls, item: tuple[Any, Any]) -> Any:
            warnings.warn(
                "'OmitIf' is deprecated and will be removed in a future version (2026). "
                "Use 'OmitIfType' instead.",
                DeprecationWarning,
                stacklevel=2
            )
            super().__class_getitem__(item)


    class OmitIfTypeValue:
        """
        Clase utilizada para omitir la serialización de un campo si su valor es de los tipos o valores especificados.
        """

        def __init__(self, field_type: Any, accepted_types: Any, accepted_values: Any):
            self.field_type = field_type
            self.accepted_types = UnionUtils.ensure_tuple(accepted_types)
            self.accepted_values = UnionUtils.ensure_tuple(accepted_values)

        @classmethod
        def __class_getitem__(cls, item: tuple[Any, Any, Any]) -> Any:
            if not isinstance(item, tuple) or len(item) != 3:
                raise TypeError(
                    "OmitIfTypesOrValues expects three arguments: "
                    "OmitIfTypesOrValues[FieldType, AcceptedTypes, AcceptedValues]"
                )
            field_type, accepted_types, accepted_values = item
            return Annotated[field_type, OmitIfTypeValue(field_type, accepted_types, accepted_values)]


class _SpecialType(BaseModel):
    """Se abrirá públicamente cuando estemos seguros del nombre y la implementación."""

    model_config = ConfigDict(frozen=True)
    discriminator: Literal['Unset'] = 'Unset'

    def __bool__(self) -> False:
        return False

    def __repr__(self) -> str:
        return self.__class__.__name__ + "()"

    def __str__(self) -> str:
        return self.__repr__()


@final
class Unset(_SpecialType):
    discriminator: Literal['Unset'] = 'Unset'


@final
class Leave(_SpecialType):
    discriminator: Literal['Leave'] = 'Leave'


unset = Unset()
leave = Leave()
