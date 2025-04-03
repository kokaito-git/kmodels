from typing import final, Literal

from kmodels.models.coremodel import CoreModel


@final
class Unset(CoreModel):
    discriminator: Literal['Unset'] = 'Unset'

    def __repr__(self) -> str:
        return "<unset>"


@final
class Leave(CoreModel):
    discriminator: Literal['Leave'] = 'Leave'

    def __repr__(self) -> str:
        return "<leave>"


unset = Unset()
leave = Leave()
