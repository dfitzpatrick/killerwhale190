import asyncio
import logging
import os

import discord

from bot.pokemon.bot import PokemonBot

log = logging.getLogger(__name__)

extensions = (
    'bot.core',
    'bot.pokemon.cog'
)


class MissingConfigurationException(Exception):
    pass


def bot_task_callback(future: asyncio.Future):
    if future.exception():
        raise future.exception()


def assert_envs_exist():
    envs = (
        ('TOKEN', 'The Bot Token', str),
        ('POKEMON_API_TOKEN', 'The API Token for Pokemon Guessing', str),
        ('LOG_GUILD_ID', 'The id of the Guild to send mismatch reports to', int),
        ('LOG_TEXT_CHANNEL_ID', 'The id of the Text Channel to send mismatch reports to', int),
    )

    for e in envs:
        ident = f"{e[0]}/{e[1]}"
        value = os.environ.get(e[0])
        if value is None:
            raise MissingConfigurationException(f"{ident} needs to be defined")
        try:
            _ = e[2](value)
        except ValueError:
            raise MissingConfigurationException(f"{ident} is not the required type of {e[2]}")


async def run_bot():
    token = os.environ['TOKEN']
    intents = discord.Intents.all()
    intents.message_content = True
    intents.members = True
    bot = PokemonBot(
        intents=intents,
        command_prefix='!',
        slash_commands=True,
    )
    try:
        assert_envs_exist()
        for ext in extensions:
            await bot.load_extension(ext)
            log.debug(f"Extension {ext} loaded")

        await bot.start(token)
    finally:
        await bot.close()

loop = asyncio.new_event_loop()
try:
    future = asyncio.ensure_future(
        run_bot(),
        loop=loop
    )
    future.add_done_callback(bot_task_callback)
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    loop.close()
