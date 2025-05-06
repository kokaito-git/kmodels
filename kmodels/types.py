from typing import TypeVar, TYPE_CHECKING, Annotated, Any
from typing import final, Literal

from pydantic import BaseModel, ConfigDict

from kmodels.utils import UnionUtils

AnyType = TypeVar("AnyType")

if TYPE_CHECKING:
    OmitIfNone = Annotated[AnyType, ...]
    OmitIfUnset = Annotated[AnyType, ...]
    OmitIf = Annotated[Any, ...]
else:
    class OmitIfNone:
        def __class_getitem__(cls, item: Any) -> Any:
            return Annotated[item, OmitIfNone()]


    class OmitIfUnset:
        def __class_getitem__(cls, item: Any) -> Any:
            return Annotated[item, OmitIfUnset()]


    class OmitIf:
        def __init__(self, accepted: Any, excluded: Any):
            self.accepted = set(UnionUtils.ensure_tuple(accepted))
            self.excluded = set(UnionUtils.ensure_tuple(excluded))

        @classmethod
        def __class_getitem__(cls, item: tuple[Any, Any]) -> Any:
            if not isinstance(item, tuple) or len(item) != 2:
                raise TypeError("OmitIf expects two arguments: OmitIf[AcceptedType, ExcludedType]")
            accepted, excluded = item

            return Annotated[accepted, OmitIf(accepted, excluded)]


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
