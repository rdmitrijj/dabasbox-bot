import html


def escape(text: object) -> str:
    """Escape user-provided text for Telegram HTML parse mode (quotes need no escaping in text nodes)."""
    return html.escape(str(text), quote=False)
