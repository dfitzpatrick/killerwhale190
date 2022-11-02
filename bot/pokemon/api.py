import logging
from dataclasses import dataclass
from typing import Optional
from typing import TypeAlias, List

import aiohttp

from .protocols import PokemonGuess

log = logging.getLogger(__name__)

@dataclass
class Guess:
    label: str
    score: float


PokemonAPIResponse: TypeAlias = List[Guess]


class PokemonAPIGuesser:

    def __init__(self, api_token: str):
        self.api_url = 'https://api-inference.huggingface.co/models/Killerw/autotrain-repo-1924865143'
        self.api_token = api_token

    @property
    def auth_header(self):
        return {'Authorization': f'Bearer {self.api_token}'}

    def most_likely(self, response_results: PokemonAPIResponse) -> Optional[Guess]:
        if not response_results:
            return
        return sorted(response_results, key=lambda o: o.score, reverse=True)[0]

    async def make_guess_request(self, data: bytes) -> PokemonAPIResponse:
        async with aiohttp.ClientSession(
                headers=self.auth_header,
                raise_for_status=True,
                timeout=aiohttp.ClientTimeout(total=10)
        ) as session:
            async with session.post(self.api_url, data=data) as response:
                log.debug("made request waiting for response paylaod")
                result = await response.json()
                log.debug("Got response")
                if not result:
                    log.debug("Empty Response returned from API")
                return [Guess(**r) for r in result]

    async def guess(self, data: bytes):
        api_results = await self.make_guess_request(data)
        guess = self.most_likely(api_results)
        if guess is not None:
            guess = PokemonGuess(name=guess.label, confidence=guess.score, data=data)
        return guess
