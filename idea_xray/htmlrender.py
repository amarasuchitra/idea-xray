"""Markdown to safe HTML, shared by the local web app and the in-browser site."""

from __future__ import annotations

import re

import markdown as md

ALLOWED_TAGS = re.compile(r"<(?!/?(details|summary|sub)>|!--)")
UNSAFE_HREF = re.compile(r'href="(?!https?://|#)[^"]*"')


def render(text: str) -> str:
    """Text from strangers (complaints, product names) can't inject tags or script links."""
    out = md.markdown(ALLOWED_TAGS.sub("&lt;", text), extensions=["tables", "fenced_code"])
    return UNSAFE_HREF.sub('href="#"', out)
