from __future__ import annotations

import io
import logging
import textwrap
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import discord

from bot.pokemon.schemas import PersistentGuess

log = logging.getLogger(__name__)
if TYPE_CHECKING:
    from bot.pokemon.protocols import PokemonGuess


def generate_guess_embed_and_file(guess: PokemonGuess, title=None, description=None) -> (discord.File, discord.Embed):
    description = description or textwrap.dedent(
        f"""
        A wild pokémon has appeared!
        Guess the pokémon and type `@Pokétwo#8236 catch {guess.name}` to catch it!"
        """
    )

    image_filename = f"{guess.name}.png"
    log.info(f"Guess data is {type(guess.data)}")
    image = discord.File(fp=io.BytesIO(guess.data), filename=image_filename)
    embed = discord.Embed(
        color=discord.Color.greyple(),
        title=title or "Pokémon Identified!",
        description=description
    )
    embed.set_image(url=f"attachment://{image_filename}")
    return image, embed


def make_guesses_persistent(message_to_attach_to: discord.Message, guesses: List[PokemonGuess]) -> List[PersistentGuess]:
    result = []
    for guess in guesses:
        result.append(PersistentGuess(
            name=guess.name,
            confidence=guess.confidence,
            custom_id=str(uuid4()),
            guild_id=message_to_attach_to.guild.id,
            channel_id=message_to_attach_to.channel.id,
            message_id=message_to_attach_to.id,
            created=datetime.now(),
            utf_data=guess.data.decode('ISO-8859-1')

        ))
    return result

