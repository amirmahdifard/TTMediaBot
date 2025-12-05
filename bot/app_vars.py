from __future__ import annotations
import os
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from bot.translator import Translator

app_name = "Player"
app_version = "2.1.1"
client_name = app_name + "-V" + app_version
about_text: Callable[[Translator], str] = lambda translator: translator.translate(
    """\
A media streaming bot for TeamTalk.
Author: amirmahdifard.
Telegram ID: @amirmahdifard\
License: Mit License\
"""
)
fallback_service = "yt"
loop_timeout = 0.01
max_message_length = 512
recents_max_lenth = 32
tt_event_timeout = 2

directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
