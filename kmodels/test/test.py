from __future__ import annotations

from typing import Any

from pydantic import SerializeAsAny, model_validator
from kmodels.models.coremodel import CoreModel


def complex_test():
    # TypeModel.__auto_register__ = True

    class SampleBaseClass(CoreModel):
        # __auto_register__: ClassVar[bool] = True
        ...

    class SampleDerivedA(SampleBaseClass):
        ...

    class SampleContainerBase(CoreModel):
        # __auto_register__: ClassVar[bool] = True
        ...

    class SampleContainerA(SampleContainerBase):
        abs_field: SerializeAsAny[SampleBaseClass]

        @model_validator(mode="before")
        @classmethod
        def validate_fields(cls, data: Any) -> Any:
            if isinstance(data, dict):
                data['abs_field'] = cls.polymorphic_single(data.get('abs_field'))
            return data

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

    CoreModel.register((SampleDerivedA, SampleContainerA))

    print('__class_registry__:', CoreModel.__class_registry__)

    print('1. Jerarquía sencilla sin muchas complicaciones')
    derived_a = SampleDerivedA()
    container_a = SampleContainerA(abs_field=derived_a)
    print(container_a)

    dumped = container_a.model_dump()
    print(dumped)

    cc2 = SampleContainerA.model_validate(dumped)
    print(cc2)

    print('\n2. Jerarquía anidada con nuevos campos')
    super_container = ContainerOfAbstractContainers(
        abs_field=container_a,
        dict_fields={'test': container_a, 'test2': container_a},
        list_field=[derived_a, derived_a],
        tuple_field=(derived_a, derived_a),
    )
    print(super_container)

    dumped = super_container.model_dump()
    print(dumped)

    super_container2 = ContainerOfAbstractContainers.model_validate(dumped)
    print(super_container2)

    print(CoreModel.__class_registry__)


def simple_test():
    class User(CoreModel):
        name: str

    class DiscordUser(User):
        description: str

    class UserBundle(CoreModel):
        users: tuple[User, ...]
        users_dict: SerializeAsAny[dict[str, User]]

        @model_validator(mode="before")
        @classmethod
        def _handle_polymorphic_fields(cls, data: Any) -> Any:
            field_name = 'users'
            _users = data.get(field_name)
            if _users is not None:
                data[field_name] = cls.polymorphic_iterable(_users, generator=tuple)

            field_name = 'users_dict'
            _users_dict = data.get(field_name)
            if _users_dict is not None:
                data[field_name] = cls.polymorphic_dict(_users_dict, value=True, generator=dict)

            return data

    DiscordUser.register()

    user = DiscordUser(
        name='火星「マールス」',
        description='''Developer
Computer science student
日本語を勉強してる'''
    )

    users_dict = {'kasei': user}

    user_bundle = UserBundle(users=(user,), users_dict=users_dict)
    print('user_bundle', user_bundle)
    json_data = user_bundle.model_dump_json(indent=2)
    print('json_data', json_data)
    rebuild_of_bundle = UserBundle.model_validate_json(json_data)
    print('rebuild_of_bundle', rebuild_of_bundle)


def test_omit_if():
    from kmodels.types import OmitIf, OmitIfNone, OmitIfUnset, Unset, unset
    class Testing(CoreModel):
        model_config = dict(strict=True)

        test_a: OmitIf[int | None, None] = None
        test_b: OmitIfNone[int | None] = None
        test_c: OmitIfUnset[int | Unset] = unset

    test = Testing(test_a=None)
    print(repr(test))
    print(test.model_dump())


def test_module_name():
    from typing import Generic, TypeVar
    from pydantic import Field
    INTEGER = TypeVar('INTEGER', bound=int)

    class IntegerBase(CoreModel, Generic[INTEGER]):
        ...

    class Integer(IntegerBase[int]):
        ...

    class Testing(CoreModel):
        __cls_discriminator__ = 'A'
        b: str = 'B'
        a: str | int = 'A'
        integer: Integer = Field(default_factory=Integer)

    def make_another_testing():
        class Testing(CoreModel):
            b: str = 'B'
            a: str | int = 'A'
            integer: Integer = Field(default_factory=Integer)

        return Testing

    Testing2 = make_another_testing()
    Testing.register()
    Testing2.register()

    print(CoreModel.__class_registry__.keys())


if __name__ == '__main__':
    # complex_test()
    # simple_test()
    # test_omit_if()
    test_module_name()
