import logging
import re
from typing import Optional
from .events import FlowEvent


class MermaidFormatter(logging.Formatter):
    """
    Custom formatter to convert FlowEvents into Mermaid sequence diagram syntax.
    """

    def format(self, record: logging.LogRecord) -> str:
        # 1. Retrieve the FlowEvent
        event: Optional[FlowEvent] = getattr(record, "flow_event", None)

        if not event:
            # Fallback for standard logs if they accidentally reach this handler
            return super().format(record)

        # 2. Convert event to Mermaid line
        return self._to_mermaid_line(event)

    def _to_mermaid_line(self, event: FlowEvent) -> str:
        """
        Converts a FlowEvent into a Mermaid syntax string.
        """
        # Sanitize participant names to avoid syntax errors in Mermaid
        src = self._sanitize(event.source)
        tgt = self._sanitize(event.target)

        # Determine arrow type
        # ->> : Solid line with arrowhead (synchronous call)
        # -->> : Dotted line with arrowhead (return)
        # --x : Dotted line with cross (error)
        arrow = "-->>" if event.is_return else "->>"

        msg = ""
        if event.is_error:
            arrow = "--x"
            msg = f"Error: {event.error_message}"
        elif event.is_return:
            # For returns, we usually show the return value or just "Return"
            msg = f"Return: {event.result}" if event.result else "Return"
        else:
            # For calls, we show Action(Params) or just Action
            msg = f"{event.message}({event.params})" if event.params else event.message

        # Optional: Add note or group if trace_id changes (not implemented in single line format)
        # For now, we just output the interaction.

        # Escape message for Mermaid safety (e.g. replacing newlines)
        msg = self._escape_message(msg)

        # Format: Source->>Target: Message
        return f"{src}{arrow}{tgt}: {msg}"

    def _sanitize(self, name: str) -> str:
        """
        Sanitizes participant names to be valid Mermaid identifiers.
        Allows alphanumeric and underscores. Replaces others.

        Mermaid doesn't like spaces or special characters in participant aliases
        unless they are quoted (which we are not doing here for simplicity),
        so we replace them with underscores.
        """
        # Replace any non-alphanumeric character (except underscore) with underscore
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        # Ensure it doesn't start with a digit (Mermaid doesn't like that sometimes, though often okay)
        if clean_name and clean_name[0].isdigit():
            clean_name = "_" + clean_name
        return clean_name

    def _escape_message(self, msg: str) -> str:
        """
        Escapes special characters in the message text.
        Mermaid messages can contain most chars, but : and newlines can be tricky.
        """
        # Replace newlines with <br/> for Mermaid display
        msg = msg.replace("\n", "<br/>")
        # We might want to escape other chars if needed, but usually text after : is forgiving.
        return msg
