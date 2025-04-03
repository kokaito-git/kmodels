from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Any, ClassVar, Type, Iterable, TypeVar
from pydantic import BaseModel, model_validator, Field, model_serializer, PlainSerializer
from typeguard import typechecked

from kmodels.types import OmitIfNone


class _CustomSerializator(BaseModel, ABC):
    def _get_skip_if_none_fields(self) -> set[str]:
        """
        Averigua que fields deben ser omitidos si son None por ser OmitIfNone
        """
        return {
            name
            for name, field_info in self.model_fields.items()
            if any(isinstance(metadata, OmitIfNone) for metadata in field_info.metadata)
        }

    def _get_serialize_aliases(self) -> dict[str, str]:
        """
        Crea un diccionario de alias a partir de self.model_fields()
        """
        return {
            name: field_info.serialization_alias
            for name, field_info in self.model_fields.items()
            if field_info.serialization_alias
        }

    @model_serializer
    def _core_serializer(self) -> dict[str, Any]:
        """
        Serializador personalizado que omite los miembros OmitIfNone si es que son None
        """
        skip_if_none = self._get_skip_if_none_fields()
        serialize_aliases = self._get_serialize_aliases()

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


class _PrivateCoreModel(_CustomSerializator, ABC):
    __class_registry__: ClassVar[dict[str, Type[CoreModel]]] = {}
    __auto_register__: ClassVar[bool] = False

    __cls_key_name__: ClassVar[str] = 'cls_key'
    cls_key: OmitIfNone[str | None] = Field(default=None)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        """
        Incorpora la funcionalidad de registrar las subclases automáticamente si __auto_register__ == True.
        Si no se quiere/puede utilizar en una rama de clases entonces puedes usar CoreModel.register(CLASE) o
        simplemente CLASE.register() con las clases que lo requieran.
        """
        super().__pydantic_init_subclass__(**kwargs)
        if cls.__auto_register__ and not cls.is_registered():
            cls.register()

    @model_validator(mode="before")
    @classmethod
    def _cls_key_handler(cls, data: Any) -> Any:
        """
        Si la clase está registrada:
        - Asigna automáticamente cls_key.
        Si la clase no está registrada:
        - Lanza excepción si se ha indicado cls_key.
        - Lanza excepción si el cls_key
        """
        if isinstance(data, dict):
            # Autoasignar cls_key si la clase está registrada y cls_key es None
            cls_key = data.get(cls.__cls_key_name__)
            valid_cls_key = cls.generate_cls_key()

            # Si data no contiene cls_key lo deducimos para averiguar si la clase está registrada
            if cls_key is None:
                # Si está registrada entonces agregamos el cls_key a la data
                if cls.is_registered(valid_cls_key):
                    data[cls.__cls_key_name__] = valid_cls_key
                return data

            # data contiene cls_key (no es None)
            # El cls_key debe ser válido
            if cls_key != valid_cls_key:
                raise ValueError(
                    f"El cls_key indicado no es válido. Trata de no asignar este valor manualmente "
                    f"(cls_key={cls_key}, valid_cls_key={valid_cls_key})\n\t"
                )
            # La clase debe estar registrada
            if not cls.is_registered(cls_key):
                # Si type_key está definido entonces validamos que la clase esté registrada
                raise ValueError(f"La clase '{cls_key}' no está registrada.")

        return data

    @classmethod
    def _register_single(cls, target_class: Type[CoreModel]):
        """
        Registra target_class.
        """
        cls_key = target_class.generate_cls_key()
        if cls_key in cls.__class_registry__:
            raise KeyError(f"La clase '{cls_key}' ya está registrada.")
        cls.__class_registry__[cls_key] = target_class

    @classmethod
    @abstractmethod
    def register(cls, target_classes: Type[CoreModel] | Iterable[Type[CoreModel]] | None = None) -> None:
        ...

    @classmethod
    @abstractmethod
    def is_registered(cls, cls_key: str | None = None) -> bool:
        ...

    @classmethod
    @abstractmethod
    def generate_cls_key(cls) -> str:
        ...


class CoreModel(_PrivateCoreModel):
    @classmethod
    def is_registered(cls, cls_key: str | None = None) -> bool:
        """
        Retorna True si la clase está registrada.
        (TIP: Puedes obtener cls_key mediante Clase.cls_key)
        """
        if cls_key is None:
            cls_key = cls.generate_cls_key()
        return cls_key in cls.__class_registry__

    @typechecked
    @classmethod
    def register(cls, target_classes: Type[CoreModel] | Iterable[Type[CoreModel]] | None = None) -> None:
        """

        """
        if target_classes is None:
            target_classes = (cls,)
        elif isinstance(target_classes, CoreModel):
            target_classes = (target_classes,)

        for tgt_class in target_classes:
            cls._register_single(tgt_class)

    @classmethod
    def get_registered_class(cls, cls_key: str) -> Type[CoreModel]:
        """
        Obtiene la clase asociada al cls_key o lanza excepción KeyError en caso de no encontrarse.
        (TIP: Puedes obtener cls_key mediante Clase.cls_key)
        """
        if not cls.is_registered(cls_key):
            raise KeyError(f"Unknown or missing class_name: {cls_key}")
        target_cls = cls.__class_registry__[cls_key]

        # Puede que sea necesario sino remover en un futuro
        # if AbstractUtils.is_abstract(target_cls):
        #     raise IsAbstract(f"Cannot use abstract class {cls_key} directly.")
        return target_cls

    @classmethod
    def generate_cls_key(cls) -> str:
        """
        Genera una key única para cada clase que va a funcionar incluso con tipos genéricos.
        """
        type_params = getattr(cls, '__pydantic_generic_metadata__', {}).get('args', ())
        if type_params:
            return f"{cls.__name__}[{','.join(tp.__name__ for tp in type_params)}]"
        return cls.__name__

    @classmethod
    def polymorphic_single(cls, data: Any) -> Any:
        """
        Función auxiliar de los model_validator del usuario. Se debe usar con un miembro polimórfico como por ejemplo
        animal: Animal, y si se ha registrado previamente 'Gato' y 'Perro' y los datos se corresponden con los de un
        'Gato' entonces se usará el registro de clases para averiguar la clase correcta y construir un objeto Gato.

        users_dict: SerializeAsAny[dict[str, User]]

        ...

        @model_validator(mode="before")
        @classmethod
        def _handle_polymorphic_fields(cls, data: Any) -> dict[str, Any]:
            if isinstance(data, dict):
                field_name = 'mascota'
                _mascota = data.get(field_name)
                if _mascota is not None:
                    data[field_name] = cls.polymorphic_single(_mascota)
            return data
        """

        if isinstance(data, dict):
            cls_key = data.get(cls.__cls_key_name__)
            if cls_key is not None:
                target_cls = cls.__class_registry__[cls_key]
                return target_cls(**data)
        return data

    @classmethod
    def polymorphic_iterable(cls, data: Iterable, *, generator: Any = tuple) -> Any:
        """
        Función auxiliar de los model_validator del usuario. Similar a polymorphic_single, pero ayuda con los iterables
        en general. Debes usar generator para especificar el tipo de salida (eg. list, tuple, etc.).
        """
        deserialized = (cls.polymorphic_single(item) for item in data)
        if generator is not None:
            return generator(deserialized)
        return

    @classmethod
    def polymorphic_dict(cls, data: Any, *, key: bool = False, value: bool = False, generator: Any = dict) -> Any:
        """
        Función auxiliar de los model_validator del usuario. Similar a polymorphic_single, pero ayuda con los
        diccionarios en lugar de objetos sencillos. Hay que indicar que es polimórfico si el key, el value o ambos,
        y el tipo que se quiere construir (ej. dict, OrderedDict).

        Esta función llamará a polymorphic_single con todas las keys/valores (dependiendo de lo que sea polimórfico)
        y finalmente retornará el tipo indicado en generator.

        class ContainerOfAbstractContainers(CoreModel):
            abs_field: SerializeAsAny[SampleContainerBase]
            dict_fields: SerializeAsAny[dict[str, SampleContainerBase]]
            list_field: SerializeAsAny[list[SampleBaseClass]]
            tuple_field: SerializeAsAny[tuple[SampleBaseClass, ...]]

            @model_validator(mode="before")
            @classmethod
            def validate_fields(cls, data: Any) -> Any:
                if isinstance(data, dict):
                    deserialization_map = {
                        'abs_field': cls.polymorphic_single,
                        'dict_fields': lambda d: cls.polymorphic_dict(d, key=False, value=True, generator=dict),
                        'list_field': lambda d: cls.polymorphic_iterable(d or [], generator=list),
                        'tuple_field': lambda d: cls.polymorphic_iterable(d or (), generator=tuple),
                    }

                    for field, func in deserialization_map.items():
                        if field in data:
                            data[field] = func(data.get(field))

                return data
        """
        if not key and not value:
            return data

        deserialized = (
            (
                cls.polymorphic_single(k) if key else k,
                cls.polymorphic_single(v) if value else v,
            ) for k, v in data.items()
        )

        if generator is not None:
            return generator(deserialized)
        return deserialized


CoreModelT = TypeVar('CoreModelT', bound=CoreModel)
