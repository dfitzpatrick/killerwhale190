import io
import logging
import os
import textwrap
from datetime import datetime
from typing import List
from uuid import uuid4

import aiohttp
import discord
import validators
from discord.ext import commands

from bot.pokemon.api import PokemonAPIGuesser
from bot.pokemon.bot import PokemonBot
from bot.pokemon.protocols import PokemonGuesser, PokemonGuess
from bot.pokemon.services import generate_guess_embed_and_file, make_guesses_persistent
from bot.pokemon.view import ReportMismatchView, PersistentGuess

log = logging.getLogger(__name__)


class PokemonGuessCog(commands.Cog):
    def __init__(self, bot: PokemonBot, guesser: PokemonGuesser):
        self.bot = bot
        self.guesser = guesser

    def is_image_url(self, content: str):
        image_types = ('tif', 'tiff', 'bmp', 'jpg', 'jpeg', 'gif', 'png')
        if content[-3:] in image_types:
            try:
                return validators.url(content)
            except validators.ValidationFailure:
                return False
        return False

    async def download_from_url(self, url: str):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url) as response:
                data = await response.read()
                return data

    def make_reply_payload(self, guesses: List[PokemonGuess]) -> (List[discord.File], List[discord.Embed]):
        files = []
        embeds = []
        views = []
        for guess in guesses[:10]:
            # Discord limitation to 10. This shouldn't  happen anyway.
            f, e = generate_guess_embed_and_file(guess)
            files.append(f)
            embeds.append(e)

        return files, embeds

    async def get_guesses(self, urls: List[str]) -> List[PokemonGuess]:
        results = []
        for url in urls:
            try:
                data = await self.download_from_url(url)
                guess = await self.guesser.guess(data)
                results.append(guess)

            except aiohttp.ClientResponseError as e:
                log.error(e)
                continue
        return results




    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        log.debug(message)
        urls = []
        # Ran into an interesting bug where sometimes Message.embed is not populated on the first send,
        # but is populated after that. Check to see if the string itself is a valid url
        if self.is_image_url(message.content):
            urls = [message.content]
        else:
            if message.attachments:
                urls.extend(a.url for a in message.attachments)
            for embed in message.embeds:
                if embed.type == 'image':
                    urls.append(embed.url)
                else:
                    if embed.image is not None and embed.image.url is not None:
                        urls.append(embed.image.url)
        log.debug("Getting guesses")
        log.debug(urls)
        guesses = await self.get_guesses(urls)
        if not guesses:
            log.debug("No guesses found")
            return
        if len(guesses) == 1:
            response = f"I spot a wild {guesses[0].name}"
        else:
            multiple = ' and a '.join(g.name for g in guesses)
            response = f"Look at all of them! A {multiple}"

        files, embeds = self.make_reply_payload(guesses)
        persistent_guesses =make_guesses_persistent(message, guesses)
        view = ReportMismatchView(self.bot, persistent_guesses)
        view.message = await message.reply(files=files, embeds=embeds, view=view)
        await self.bot.add_persistent_view(view.message.id, persistent_guesses)

async def setup(bot: commands.Bot):
    guesser = PokemonAPIGuesser(api_token=os.environ['POKEMON_API_TOKEN'])
    await bot.add_cog(PokemonGuessCog(bot, guesser))

