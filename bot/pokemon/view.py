from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional, Callable, TYPE_CHECKING

import discord
from discord import ui, Interaction

from bot.pokemon.protocols import PokemonGuess
from bot.pokemon.schemas import PersistentGuess
from bot.pokemon.services import generate_guess_embed_and_file

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from bot.pokemon.bot import PokemonBot




class MismatchButton(ui.Button):

    def __init__(self, bot: PokemonBot, persistent_guess: PersistentGuess, disabler: Callable, **kwargs):
        super(MismatchButton, self).__init__(**kwargs)
        self.bot = bot
        self.persistent_guess = persistent_guess
        self.disabler = disabler



    async def callback(self, itx: Interaction):
        msg = f"{itx.user.name}/{itx.user.id} from Guild {itx.guild.name}/{itx.guild.id} Reported this as a mismatch:\n\n {self.persistent_guess.name}"
        target_guild_id = int(os.environ['LOG_GUILD_ID'])
        target_channel_id = int(os.environ['LOG_TEXT_CHANNEL_ID'])
        guild = self.bot.get_guild(target_guild_id)
        if guild is None:
            log.error("Logging Guild not found in Bot cache")
            return
        channel = guild.get_channel(target_channel_id)
        if channel is None:
            log.error("Found Logging Guild but Logging Channel not found in Bot cache. Does this channel exist?")
            return
        guess = PokemonGuess(name=self.persistent_guess.name, data=self.persistent_guess.utf_data.encode('ISO-8859-1'), confidence=self.persistent_guess.confidence)
        f, e = generate_guess_embed_and_file(guess=guess, description=msg, title="Mismatch Reported")
        self.disabled = True
        await channel.send(file=f, embed=e)
        await itx.response.send_message("Report sent", ephemeral=True)
        await self.bot.remove_persistent_view(itx.message.id)
        self.disabler(self)


class ReportMismatchView(ui.View):

    message: Optional[discord.Message | discord.PartialMessage] = None

    def __init__(self, bot: PokemonBot, guesses: List[PersistentGuess]):
        self.guesses = guesses
        self.bot = bot
        super(ReportMismatchView, self).__init__(timeout=None)

        for guess in guesses:
            label = f"Report Mismatch on {guess.name}"
            btn = MismatchButton(self.bot, guess, label=label, custom_id=guess.custom_id, style=discord.ButtonStyle.red, disabler=self.remove_item)
            self.add_item(btn)

        loop = asyncio.get_running_loop()
        loop.create_task(self.auto_timeout_view())

    async def remove_view(self):
        log.debug(self.message)
        if self.message is None:
            log.error("Could not remove view due to missing message")
            return

        await self.bot.remove_persistent_view(self.message.id)
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    async def auto_timeout_view(self):
        log.debug(self.guesses[0].created)
        target = self.guesses[0].created + timedelta(seconds=os.environ.get('VIEW_TIMEOUT', 60))
        if datetime.now() > target:
            log.debug('remove expired')
            await self.remove_view()
            return
        await discord.utils.sleep_until(target)
        await self.remove_view()




