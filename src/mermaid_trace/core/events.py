from dataclasses import dataclass, field
import time
from typing import Optional


@dataclass
class FlowEvent:
    """
    Represents a single interaction or step in the execution flow.

    This data structure acts as the intermediate representation (IR) between
    runtime code execution and the final Mermaid diagram output. Each instance
    corresponds directly to one arrow or note in the sequence diagram.

    The fields map to Mermaid syntax components as follows:
    `source` -> `target`: `message`

    Attributes:
        source (str):
            The name of the participant initiating the action (the "Caller").
            In Mermaid: The participant on the LEFT side of the arrow.

        target (str):
            The name of the participant receiving the action (the "Callee").
            In Mermaid: The participant on the RIGHT side of the arrow.

        action (str):
            A short, human-readable name for the operation (e.g., function name).
            Used for grouping or filtering logs, but often redundant with message.

        message (str):
            The actual text label displayed on the diagram arrow.
            Example: "getUser(id=1)" or "Return: User(name='Alice')".

        timestamp (float):
            Unix timestamp (seconds) of when the event occurred.
            Used for ordering events if logs are processed asynchronously,
            though Mermaid sequence diagrams primarily rely on line order.

        trace_id (str):
            Unique identifier for the trace session.
            Allows filtering multiple concurrent traces from a single log file
            to generate separate diagrams for separate requests.

        is_return (bool):
            Flag indicating if this is a response arrow.
            If True, the arrow is drawn as a dotted line (`-->`) in Mermaid.
            If False, it is a solid line (`->`) representing a call.

        is_error (bool):
            Flag indicating if an exception occurred.
            If True, the arrow might be styled differently (e.g., `-x`) to show failure.

        error_message (Optional[str]):
            Detailed error text if `is_error` is True.
            Can be added as a note or included in the arrow label.

        params (Optional[str]):
            Stringified representation of function arguments.
            Captured only for request events (call start).

        result (Optional[str]):
            Stringified representation of the return value.
            Captured only for return events (call end).
    """

    source: str
    target: str
    action: str
    message: str
    trace_id: str
    timestamp: float = field(default_factory=time.time)
    is_return: bool = False
    is_error: bool = False
    error_message: Optional[str] = None
    params: Optional[str] = None
    result: Optional[str] = None
