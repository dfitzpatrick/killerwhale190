from __future__ import annotations

import json
import logging
import os
from typing import List

from discord.ext import commands

from bot.config import ConfigMixin
from bot.pokemon.schemas import PersistentGuess
from bot.pokemon.view import ReportMismatchView

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../', 'static'))
FILE_PATH = os.path.normpath(f'{BASE_DIR}/settings.json')

log = logging.getLogger(__name__)


class PokemonBot(ConfigMixin, commands.Bot):

    def __init__(self, **kwargs):
        super(PokemonBot, self).__init__(**kwargs)

    async def add_persistent_view(self, message_attached_to_id: int, persistent_guesses: List[PersistentGuess]):
        self.config_settings['views'][str(message_attached_to_id)] = [g.json() for g in persistent_guesses]
        await self.save_settings()

    async def remove_persistent_view(self, message_attached_to_id: int):
        try:
            del self.config_settings['views'][str(message_attached_to_id)]
        except KeyError:
            pass
        finally:
            await self.save_settings()

    async def _load_persistent_views(self):
        cleanup_ids = []
        for message_id, guesses in self.config_settings.get('views', {}).items():
            persistent_guesses = [PersistentGuess(**json.loads(pg)) for pg in guesses]
            item = persistent_guesses[0]
            view = ReportMismatchView(self, persistent_guesses)
            channel = self.get_partial_messageable(item.channel_id, guild_id=item.guild_id)
            if channel is None:
                cleanup_ids.append(message_id)
                return
            message = channel.get_partial_message(message_id)
            if message is None:
                cleanup_ids.append(message_id)
                return
            view.message = message
            self.add_view(view)
        for message_id in cleanup_ids:
            await self.remove_persistent_view(message_id)

    async def setup_hook(self) -> None:
        if self.config_settings.get('views') is None:
            self.config_settings['views'] = {}
            await self.save_settings()
        # In case you need. With a timeout we don't need to do this
        await self._load_persistent_views()

