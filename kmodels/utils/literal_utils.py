from typing import Type, get_origin, Literal, get_args, Any, Iterable, Optional, Union


class LiteralUtils:
    """
    TODO: Queda trabajo en esta clase.
    """

    @staticmethod
    def is_literal(tp: Any):
        return get_origin(tp) is Literal

    @staticmethod
    def _get_args(tp: Any) -> tuple[Any, ...]:
        """Devuelve una tupla con los valores de un Literal. Esta función solo está para recordar como hacerlo."""
        return get_args(tp)

    @staticmethod
    def extract_literals(iterable: Iterable) -> tuple[type, ...]:
        """
        Extrae los tipos de los Literals encontrados en el iterable.
        (No remueve los duplicados porque es una perdida de eficiencia tratar de hacer eso en la mayoría de los casos).
        """
        extracted_literals = []
        for item in iterable:
            if LiteralUtils.is_literal(item):
                extracted_literals.append(item)
        return tuple(extracted_literals)

    @staticmethod
    def value_in_literals(value: Any, literals: Iterable[type[Literal]]) -> bool:
        """Extrae los valores de los literales y comprueba si el valor está dentro de alguno de ellos."""
        for lit in literals:
            if not LiteralUtils.is_literal(lit):
                raise TypeError(f"Expected a Literal, got {type(lit)}")
            values = get_args(lit)
            if value in values:
                return True
        return False
