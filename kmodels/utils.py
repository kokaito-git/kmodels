from __future__ import annotations

import inspect
import types
from abc import ABC
from typing import Type, get_origin, Any, Union, get_args
from kmodels.error import IsAbstract


# Utilidad para manejar clases abstractas
class AbstractUtils:
    @classmethod
    def is_abstract(cls, target_class: Type):
        return inspect.isabstract(target_class) or ABC in target_class.__bases__

    @classmethod
    def raise_abstract_class(cls, target_class: Type):
        if cls.is_abstract(target_class):
            cname = target_class.__name__
            raise IsAbstract(f"{cname} is an abstract class (inherits from ABC) and you cannot instantiate it.")


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

# # Utilidad para manejar la validación de class_name
# class ClassNameUtils:
#     @classmethod
#     def validate_class_name(cls, target_class: Type):
#         # Detectar si es una clase genérica intermedia generada por Pydantic
#         is_generic_intermediate = '[' in target_class.__name__ and ']' in target_class.__name__
#         if is_generic_intermediate:
#             return
#
#         # Si es una clase abstracta, no aplicar validación
#         if cls.is_abstract(target_class):
#             return
#
#         # Validar la existencia y tipo de class_name
#         class_name_annotation = target_class.__annotations__.get('class_name', None)
#
#         if class_name_annotation is None:
#             raise AttributeError(
#                 f'Si {target_class.__name__} es abstracta entonces debe heredar de ABC o definir al menos un método '
#                 f'abstracto, si no lo es entonces debes definirle el atributo class_name de la siguiente manera:\n'
#                 f'\tclass_name: Literal["{target_class.__name__}"] = "{target_class.__name__}"'
#             )
#
#         # noinspection PyUnresolvedReferences
#         class_name_type = target_class.model_fields['class_name'].annotation
#
#         origin_type = get_origin(class_name_type)
#         if origin_type is not Literal:
#             raise AttributeError(
#                 f"El atributo 'class_name' en la clase {target_class.__name__} debe ser un Literal con el valor "
#                 f"exacto del nombre de la clase.\n"
#                 f"\t(Definición de tipo esperada)\n\t\tclass_name: Literal['{target_class.__name__}'] = '{target_class.__name__}'\n"
#                 f"\t(Definición de tipo encontrada)\n\t\tclass_name: {class_name_annotation} ..."
#             )
#
#         literal_args = list(get_args(class_name_type))
#         if len(literal_args) != 1:
#             raise AttributeError(
#                 f"El atributo 'class_name' en la clase {target_class.__name__} debe ser un Literal con un único valor,\n"
#                 f"pero se encontraron múltiples opciones: {literal_args}\n"
#                 f"\t(Definición esperada)\n\t\tclass_name: "
#                 f"Literal['{target_class.__name__}'] = '{target_class.__name__}'\n"
#                 f"\t(Definición encontrada)\n\t\tclass_name: Literal{literal_args}"
#             )
#
#         if literal_args[0] != target_class.__name__:
#             raise AttributeError(
#                 f"El atributo 'class_name' en la clase {target_class.__name__} debe ser un Literal con el valor exacto de su nombre.\n"
#                 f"\t(Definición esperada)\n\t\tclass_name: Literal['{target_class.__name__}'] = '{target_class.__name__}'\n"
#                 f"\t(Definición encontrada)\n\t\tclass_name: Literal['{literal_args[0]}'] = '{literal_args[0]}'"
#             )
#
#     @classmethod
#     def is_abstract(cls, target_class: Type):
#         return AbstractUtils.is_abstract(target_class)
