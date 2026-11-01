"""Defuddle web_extract backend (user plugin, installed to ``$HERMES_HOME/plugins/web/defuddle``)."""
from __future__ import annotations

from .provider import DefuddleExtractProvider


def register(ctx) -> None:
    ctx.register_web_search_provider(DefuddleExtractProvider())
