#!/usr/bin/env python

# SPDX-License-Identifier: BSD-3-Clause

# Convert Markdown into a format that reads nice as YouTube video description.
# It e.g. parses Links as `Link name (https://actual.link/)` or bullet lists
# always with dashes. Images are ignored.
#
# You need to have `mistune` (https://pypi.org/project/mistune/) installed in
# order to use this script. This is a command line utility to convert a
# Markdown file as well as a library that exports `YouTubeRenderer` which can
# be used by mistune.

# This code is based on mistune, hence it's licensed under the BSD License.

from html.parser import HTMLParser
import re
import sys
from typing import Any, Dict, Iterable, cast
from textwrap import indent

import mistune
from mistune import BaseRenderer, BlockState


def strip_end(src: str) -> str:
    return re.compile(r"\\n\s+$").sub("\\n", src)


class ExtractHref(HTMLParser):
    href = None

    def handle_starttag(self, tag, attrs):
        for attr, value in attrs:
            if attr == "href":
                self.href = value
                return


class YouTubeRenderer(BaseRenderer):
    """A renderer to convert into YouTube descriptions."""

    NAME = "YouTube description"
    # When parsing raw HTML links we have the link before the text, hence
    # buffer it.
    href = None

    def __call__(
        self, tokens: Iterable[Dict[str, Any]], state: BlockState
    ) -> str:
        out = self.render_tokens(tokens, state)
        # special handle for line breaks
        out += "\\n\\n".join(self.render_referrences(state)) + "\\n"
        return strip_end(out)

    def render_referrences(self, state: BlockState) -> Iterable[str]:
        # References are just dropped as we render links inline.
        yield ""

    def render_children(self, token: Dict[str, Any], state: BlockState) -> str:
        children = token["children"]
        return self.render_tokens(children, state)

    def text(self, token: Dict[str, Any], state: BlockState) -> str:
        return cast(str, token["raw"])

    def emphasis(self, token: Dict[str, Any], state: BlockState) -> str:
        return "_" + self.render_children(token, state) + "_"

    def strong(self, token: Dict[str, Any], state: BlockState) -> str:
        return "*" + self.render_children(token, state) + "*"

    def link(self, token: Dict[str, Any], state: BlockState) -> str:
        text = self.render_children(token, state)
        url = token["attrs"]["url"]

        # If the text and the URL are the same, just return the URL.
        if text == url:
            return url
        else:
            return f"{text} ({url})"

    def image(self, token: Dict[str, Any], state: BlockState) -> str:
        # Images are not included in the description.
        return ""

    def codespan(self, token: Dict[str, Any], state: BlockState) -> str:
        return "`" + cast(str, token["raw"]) + "`"

    def linebreak(self, token: Dict[str, Any], state: BlockState) -> str:
        return "\\n"

    def softbreak(self, token: Dict[str, Any], state: BlockState) -> str:
        return "\\n"

    def blank_line(self, token: Dict[str, Any], state: BlockState) -> str:
        return ""

    def inline_html(self, token: Dict[str, Any], state: BlockState) -> str:
        # Try to parse tags that can be easily supported with Markdown.
        # Output the raw HTML as text for all other cases. It's not that
        # beautiful, but it's better than losing information.

        # Matching the tag name of opening and closing tags.
        tag = re.search("</?([a-zA-Z0-9]+)", token["raw"])[1].lower()

        if tag in ["b", "strong"]:
            return "*"
        elif tag in ["i", "em"]:
            return "_"
        elif tag in ["s", "del", "strike"]:
            return "-"
        elif tag == "br":
            return "\\n"
        elif tag == "a":
            if token["raw"].startswith("</"):
                return f" ({self.href})"
            else:
                href = re.search("</?([a-zA-Z0-9])", token["raw"])[1].lower()
                parser = ExtractHref()
                parser.feed(token["raw"])
                if parser.href is not None:
                    self.href = parser.href
                    return ""

        return cast(str, token["raw"])

    def paragraph(self, token: Dict[str, Any], state: BlockState) -> str:
        text = self.render_children(token, state)
        return text + "\\n\\n"

    def heading(self, token: Dict[str, Any], state: BlockState) -> str:
        level = cast(int, token["attrs"]["level"])
        marker = "#" * level
        text = self.render_children(token, state)
        return marker + " " + text + "\\n\\n"

    def thematic_break(self, token: Dict[str, Any], state: BlockState) -> str:
        return "***\\n\\n"

    def block_text(self, token: Dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state) + "\\n"

    def block_code(self, token: Dict[str, Any], state: BlockState) -> str:
        attrs = token.get("attrs", {})
        info = cast(str, attrs.get("info", ""))
        code = cast(str, token["raw"])
        return f"```{info}\\n{code}```\\n\\n"

    def block_quote(self, token: Dict[str, Any], state: BlockState) -> str:
        text = indent(self.render_children(token, state), "> ")
        return text + "\\n\\n"

    def block_html(self, token: Dict[str, Any], state: BlockState) -> str:
        return cast(str, token["raw"]) + "\\n\\n"

    def block_error(self, token: Dict[str, Any], state: BlockState) -> str:
        return ""

    def list(self, token: Dict[str, Any], state: BlockState) -> str:
        return render_list(self, token, state)


def render_list(
    renderer: "BaseRenderer", token: Dict[str, Any], state: "BlockState"
) -> str:
    attrs = token["attrs"]
    if attrs["ordered"]:
        children = _render_ordered_list(renderer, token, state)
    else:
        children = _render_unordered_list(renderer, token, state)

    text = "".join(children)
    parent = token.get("parent")
    if parent:
        if parent["tight"]:
            return text
        return text + "\\n"
    return strip_end(text) + "\\n"


def _render_list_item(
    renderer: "BaseRenderer",
    parent: Dict[str, Any],
    item: Dict[str, Any],
    state: "BlockState",
) -> str:
    leading = cast(str, parent["leading"])
    text = ""
    for tok in item["children"]:
        if tok["type"] == "list":
            tok["parent"] = parent
        elif tok["type"] == "blank_line":
            continue
        text += renderer.render_token(tok, state)

    lines = text.splitlines()
    text = (lines[0] if lines else "") + "\\n"
    prefix = " " * len(leading)
    for line in lines[1:]:
        if line:
            text += prefix + line + "\\n"
        else:
            text += "\\n"
    return leading + text


def _render_ordered_list(
    renderer: "BaseRenderer", token: Dict[str, Any], state: "BlockState"
) -> Iterable[str]:
    attrs = token["attrs"]
    start = attrs.get("start", 1)
    for item in token["children"]:
        parent = {
            # Format all types of ordered lists as dots.
            "leading": f" {start}. ",
            "tight": token["tight"],
        }
        yield _render_list_item(renderer, parent, item, state)
        start += 1


def _render_unordered_list(
    renderer: "BaseRenderer", token: Dict[str, Any], state: "BlockState"
) -> Iterable[str]:
    parent = {
        # Format all types of unordered lists as dashes.
        "leading": " - ",
        "tight": token["tight"],
    }
    for item in token["children"]:
        yield _render_list_item(renderer, parent, item, state)


def main(argv=None):
    if argv is None:
        argv = sys.argv

    if len(argv) != 2:
        print("Usage: {} input.md".format(argv[0]))
        return 1

    input_filename = argv[1]

    format_markdown = mistune.create_markdown(renderer=YouTubeRenderer())

    with open(input_filename, "r") as input_file:
        text = input_file.read()
        result = format_markdown(text)
        print(result)


if __name__ == "__main__":
    sys.exit(main())
