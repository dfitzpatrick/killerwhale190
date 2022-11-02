import pytest
import os
import pathlib
from bot.pokemon.api import PokemonAPIGuesser, Guess
from bot.pokemon.protocols import PokemonGuess

API_TOKEN = os.environ['POKEMON_API_TOKEN']


@pytest.mark.asyncio
async def test_api_request_has_response():
    sample_image = pathlib.Path(__file__).parent / 'pokemon-pawmi.png'
    with sample_image.open(mode='rb') as f:
        data = f.read()
    guesser = PokemonAPIGuesser(api_token=API_TOKEN)
    response = await guesser.make_guess_request(data)
    assert isinstance(response, list)
    assert isinstance(response[0], Guess)

def test_find_greatest_confidence():
    guesser = PokemonAPIGuesser(api_token=API_TOKEN)
    sample = [Guess('foo', 0.13434), Guess('bar', .0012352523), Guess('correct_guess', 0.645435)]

    result = guesser.most_likely(sample)
    assert result == Guess('correct_guess', 0.645435)
    assert guesser.most_likely([]) is None


@pytest.mark.asyncio
async def test_guess():
    sample_image = pathlib.Path(__file__).parent / 'pokemon-pawmi.png'
    guesser = PokemonAPIGuesser(api_token=API_TOKEN)
    with sample_image.open(mode='rb') as f:
        data = f.read()
    guess = await guesser.guess(data)
    assert isinstance(guess, PokemonGuess)
    assert guess.name == 'Buizel'

