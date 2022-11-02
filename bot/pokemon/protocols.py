import io
from dataclasses import dataclass
from typing import Protocol, List, Optional


@dataclass()
class PokemonGuess:
    name: str
    data: bytes
    confidence: Optional[float] = None


class PokemonGuesser(Protocol):

    async def guess(self, data: bytes) -> Optional[PokemonGuess]:
        ...

