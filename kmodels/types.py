from typing import TypeVar, TYPE_CHECKING, Annotated, Any
from typing import final, Literal

from pydantic import BaseModel

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


@final
class Unset(BaseModel):
    discriminator: Literal['Unset'] = 'Unset'

    def __repr__(self) -> str:
        return "<unset>"


@final
class Leave(BaseModel):
    discriminator: Literal['Leave'] = 'Leave'

    def __repr__(self) -> str:
        return "<leave>"


unset = Unset()
leave = Leave()
