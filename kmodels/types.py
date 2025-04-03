from typing import TypeVar, TYPE_CHECKING, Annotated, Any

AnyType = TypeVar("AnyType")

if TYPE_CHECKING:
    OmitIfNone = Annotated[AnyType, ...]
else:
    class OmitIfNone:
        def __class_getitem__(cls, item: Any) -> Any:
            return Annotated[item, OmitIfNone()]
