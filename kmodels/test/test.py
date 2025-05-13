from __future__ import annotations
from abc import abstractmethod, ABC
from typing import Self, ClassVar, Any, Iterable, Counter, get_args, Union
from pydantic import Field, model_validator, ConfigDict
from typing_extensions import Literal
import os

from kmodels.models import CoreModel
from kmodels.types import OmitIfType, OmitIfValue, OmitIfTypeValue, Unset, unset, OmitIfNone, OmitIf

keysym_data_dir = "/home/kokaito/Insync/kokaito.git@gmail.com/Google Drive/projects/kbinds/xmodmap2/keysym/data"


class FileHelper:
    @staticmethod
    def load_file(path: str) -> str:
        _path = os.path.expanduser(path)
        with open(_path, 'r', encoding='utf-8') as file:
            return file.read()

    @staticmethod
    def save_file(path: str, content: str):
        _path = os.path.expanduser(path)
        with open(_path, 'w', encoding='utf-8') as file:
            file.write(content)


def get_duplicates[T](items: Iterable[T]) -> list[T]:
    """Función auxiliar que no está de más que retorna una lista con los elementos duplicados de un iterable. Si
    necesitas más (ej. un diccionario con la cuenta de duplicados)"""

    counts = Counter(items)
    # Filtramos solo los que aparecen más de una vez
    dups = [item for item, count in counts.items() if count > 1]
    return dups


class XKeysym(CoreModel, ABC):
    """Clase usada para representar los keysyms completos de xmodmap. xmodmap te permite asignar teclas poniendo un solo
    keysym y dependiendo de si es mayúscula o minúscula lo que tú escribas se traduce de una forma o de otra.
    Por tanto, tener una base de datos de keysyms es necesario para las traducciones así como para poder validar los
    options de los elementos (XKey, XModifier, etc.)."""
    model_config = ConfigDict(frozen=True)
    keysym: str = Field(
        description='Indica el símbolo (todos los símbolos tienen un símbolo sean mayúsculas, minúsculas o no tengan)'
    )

    comment: str | None = Field(
        default=None, description='Comentario opcional para teclas que no se entienden bien o lo que sea.'
    )

    @abstractmethod
    def get_non_mayus(self) -> str:
        ...

    @abstractmethod
    def get_minus(self) -> str | None:
        ...

    @abstractmethod
    def get_mayus(self) -> str | None:
        ...

    @abstractmethod
    def consistent_repr(self) -> str:
        ...


class XKeysymSingle(XKeysym):
    def get_non_mayus(self) -> str:
        return self.keysym

    def get_minus(self) -> None:
        return None

    def get_mayus(self) -> None:
        return None

    def consistent_repr(self, ind: str = "") -> str:
        return f"{ind}keysym: {self.keysym} -> {self.keysym}"


class XKeysymWithMayus(XKeysym, ABC):
    kind: Literal['mayus', 'minus', 'none'] = Field(
        default='none', description='Indica si el símbolo es mayúscula o minúscula'
    )

    @abstractmethod
    def get_non_mayus(self) -> str:
        ...

    @abstractmethod
    def get_minus(self) -> str:
        ...

    @abstractmethod
    def get_mayus(self) -> str:
        ...

    def consistent_repr(self, ind: str = "") -> str:
        return f"{ind}keysym: {self.keysym} -> {self.get_minus()} / {self.get_mayus()}"


class XKeysymMayus(XKeysymWithMayus):
    minus: str

    def get_non_mayus(self) -> str:
        return self.minus

    def get_minus(self) -> str:
        return self.minus

    def get_mayus(self) -> str:
        return self.keysym


class XKeysymMinus(XKeysymWithMayus):
    mayus: str

    def get_non_mayus(self) -> str:
        return self.keysym

    def get_minus(self) -> str:
        return self.keysym

    def get_mayus(self) -> str:
        return self.mayus


KEYSYMS_T = Union[XKeysymSingle, XKeysymMayus, XKeysymMinus]

DB_RESCUE_T = Literal['db', 'rescue']
DB_RESCUE = get_args(DB_RESCUE_T)


class XKeysymDatabase(CoreModel):
    model_config = ConfigDict(frozen=True)

    """Clase que contiene los keysyms así como variables para poder acceder a los diferentes datos de los keysyms de
    manera cómoda. También permite agregarlos sin romper el sistema.

    Y para colmo, permite guardarlos y cargarlos desde un archivo json."""

    __keysym_data_dir__: ClassVar[str] = keysym_data_dir
    __keysym_path__: ClassVar[str] = __keysym_data_dir__ + '/keysym.json'
    __rescue_path__: ClassVar[str] = __keysym_data_dir__ + '/keysym_rescue.json'
    __keysyms_name__: ClassVar[str] = "keysyms"
    __sym_idx_name__: ClassVar[str] = "sym_idx"
    __idx_sym_name__: ClassVar[str] = "idx_sym"

    keysyms: tuple[KEYSYMS_T, ...] = Field(default_factory=tuple)
    sym_idx: dict[str, int] = Field(default_factory=dict)
    idx_sym: dict[int, str] = Field(default_factory=dict)

    # test: OmitIfValues[str, ("hola",)] = "hola"

    test: OmitIf[None, None] = None

    # sym_idx: OmitIf[dict[str, int], dict] = Field(default_factory=dict)
    # idx_sym: OmitIf[dict[int, str], dict] = Field(default_factory=dict)

    @model_validator(mode='before')
    @classmethod
    def _append_maps(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if cls.__keysyms_name__ in data:
                data[cls.__sym_idx_name__] = {k.keysym: i for i, k in enumerate(data[cls.__keysyms_name__])}
                data[cls.__idx_sym_name__] = {i: k for k, i in data[cls.__sym_idx_name__].items()}
        return data

    @model_validator(mode='after')
    def validate_duplicates(self) -> Self:
        if len(self.keysyms) != len(set(self.keysyms)):
            duplicates = get_duplicates()
            duplicates_str = ", ".join(f'"{d}"' for d in duplicates)
            raise ValueError(f'Hay keysyms duplicados en la base de datos: [ {duplicates_str} ]')
        return self

    @classmethod
    def file_helper(cls) -> type[FileHelper]:
        return FileHelper

    @classmethod
    def path_helper(cls, path: DB_RESCUE_T | str) -> str:
        if path in DB_RESCUE:
            path = cls.__keysym_path__ if path == 'db' else cls.__rescue_path__
        return path

    @classmethod
    def load(cls, path: DB_RESCUE_T | str = 'db') -> XKeysymDatabase:
        _path = cls.path_helper(path)
        return cls.from_json(cls.file_helper().load_file(_path))

    def save(self, path: DB_RESCUE_T | str = 'db'):
        _path = self.path_helper(path)
        json_data = self.model_dump_json(indent=4)
        self.file_helper().save_file(_path, json_data)

    @classmethod
    def from_json(cls, data: str) -> Self:
        return cls.model_validate_json(data)

    def to_json(self, *, indent: int | None = 4) -> str:
        return self.model_dump_json(indent=indent)

    def __iter__(self):
        return iter(self.keysyms)

    def __contains__(self, item: str) -> bool:
        return item in self.sym_idx

    def __getitem__(self, item: str) -> XKeysym:
        return self.keysyms[self.sym_idx[item]]

    def consistent_repr(self, ind: str = "") -> str:
        ind2 = "  " + ind
        keysyms_str = "\n".join(ks.consistent_repr(ind2) for ks in self.keysyms)
        return f"{ind}{self.__class__.__name__}:\n{keysyms_str}"

    def __str__(self) -> str:
        return self.consistent_repr()


def test():
    sample_mayus = XKeysymMayus(keysym="a", minus="A")
    sample_minus = XKeysymMinus(keysym="A", mayus="a")
    sample_single = XKeysymSingle(keysym="a")

    elements = (
        sample_mayus,
        # sample_minus,
        # sample_single,
    )
    db = XKeysymDatabase(keysyms=elements)
    # print(db)
    print(db.model_dump_json(indent=4))


if __name__ == '__main__':
    test()
