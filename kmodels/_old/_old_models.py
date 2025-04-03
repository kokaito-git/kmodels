from __future__ import annotations

from typing import Any, ClassVar, Type, Iterable, TypeVar, Generic, Self
from pydantic import BaseModel, model_validator, Field, model_serializer, PlainSerializer
from typeguard import typechecked
from abc import abstractmethod, ABC
from lib.kmodels.error import IsAbstract
from lib.kmodels.types import OmitIfNone
from lib.kmodels.utils import AbstractUtils


def deserialize_single(data: Any) -> Any:
    return CoreModel.deserializer_helper(data)


def deserialize_dict(data: Any, *, key: bool, value: bool, generator: Any = dict) -> Any:
    """
    Función auxiliar que deserializa un diccionario (o algo que se comporta como él)
    :param data:
    :param key:
    :param value:
    :param generator:
    :return:
    """
    if not key and not value:
        return data

    deserialized = (
        (deserialize_single(k) if key else k, deserialize_single(v) if value else v,) for k, v in data.items()
    )

    if generator is not None:
        return generator(deserialized)
    return deserialized


def deserialize_iterable(
        data: Iterable, *,
        generator: Any = tuple
) -> Any:
    deserialized = (deserialize_single(item) for item in data)
    if generator is not None:
        return generator(deserialized)
    return deserialized


class CoreModel(BaseModel):
    __class_registry__: ClassVar[dict[str, Type[CoreModel]]] = {}
    __auto_register__: ClassVar[bool] = False

    __cls_key_name__: ClassVar[str] = 'cls_key'
    cls_key: OmitIfNone[str | None] = Field(default=None)

    @model_serializer
    def _no_serialize_exclude_if_none(self):
        skip_if_none = set()
        serialize_aliases = dict()

        # Gather fields that should omit if None
        for name, field_info in self.model_fields.items():
            # noinspection PyTypeHints
            if any(
                    isinstance(metadata, OmitIfNone) for metadata in field_info.metadata
            ):
                skip_if_none.add(name)
            elif field_info.serialization_alias:
                serialize_aliases[name] = field_info.serialization_alias

        serialized = dict()
        for name, value in self:
            # Skip serializing None if it was marked with "OmitIfNone"
            if value is None and name in skip_if_none:
                continue
            serialize_key = serialize_aliases.get(name, name)

            # Run Annotated PlainSerializer
            for metadata in self.model_fields[name].metadata:
                if isinstance(metadata, PlainSerializer):
                    value = metadata.func(value)

            serialized[serialize_key] = value

        return serialized

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        super().__pydantic_init_subclass__(**kwargs)
        if cls.__auto_register__ and not cls.is_registered():
            cls.register()

    @model_validator(mode="before")
    @classmethod
    def _type_key_handler(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Autoasignar type_key si la clase está registrada y type_key es None
            type_key = data.get(cls.__cls_key_name__)

            # Autoasignamos type_key si no está definido
            if type_key is None:
                type_key = cls.generate_type_key()
                if type_key in cls.__class_registry__:
                    data[cls.__cls_key_name__] = type_key

            elif type_key not in cls.__class_registry__:
                # Si type_key está definido entonces validamos que la clase esté registrada
                raise ValueError(f"La clase '{cls.__cls_key_name__}' no está registrada.")
        return data

    @classmethod
    def is_registered(cls, type_key: str | None = None) -> bool:
        if type_key is None:
            type_key = cls.generate_type_key()
        return type_key in cls.__class_registry__

    @classmethod
    def _register_single(cls, target_class: Type[CoreModel]):
        type_key = target_class.generate_type_key()
        if type_key in cls.__class_registry__:
            raise KeyError(f"La clase '{type_key}' ya está registrada.")
        cls.__class_registry__[type_key] = target_class

    @typechecked
    @classmethod
    def register(cls, target_classes: Type[CoreModel] | Iterable[Type[CoreModel]] | None = None) -> None:
        """
        Registra la clase manualmente en el class_registry.

        Args:
            name (str | None): Nombre opcional para registrar la clase. Si es None, se usa el nombre de la clase.
            target_classes (Type[CoreModel] | None): Clase a registrar, si no se especifica se registrará esta clase.
        """
        if target_classes is None:
            target_classes = (cls,)
        elif isinstance(target_classes, CoreModel):
            target_classes = (target_classes,)

        for tgt_class in target_classes:
            cls._register_single(tgt_class)

    @classmethod
    def get_registered_class(cls, type_key: str) -> Type[CoreModel]:
        """
        Obtiene la clase registrada a partir del nombre de clase. Revisar __pydantic_init_subclass__ para más
        información.
        """
        if not cls.is_registered(type_key):
            raise ValueError(f"Unknown or missing class_name: {type_key}")
        target_cls = cls.__class_registry__[type_key]

        if AbstractUtils.is_abstract(target_cls):
            raise IsAbstract(f"Cannot use abstract class {type_key} directly.")
        return target_cls

    @classmethod
    def generate_type_key(cls) -> str:
        type_params = getattr(cls, '__pydantic_generic_metadata__', {}).get('args', ())
        if type_params:
            return f"{cls.__name__}[{','.join(tp.__name__ for tp in type_params)}]"
        return cls.__name__

    @classmethod
    def deserializer_helper(cls, data: Any) -> Any:
        if isinstance(data, dict):
            cls_key = data.get(cls.__cls_key_name__)
            if cls_key is not None:
                target_cls = cls.__class_registry__[cls_key]
                return target_cls(**data)
        return data


CoreModelT = TypeVar('CoreModelT', bound=CoreModel)


class Modelable(Generic[CoreModelT], ABC):
    @abstractmethod
    def to_model(self) -> CoreModelT:
        pass

    @classmethod
    @abstractmethod
    def from_model(cls, model: CoreModelT) -> Self:
        ...
