import asyncio
import random
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ChatState:
    """Coalescing state for a single chat."""
    read_task: asyncio.Task | None = None
    read_done: bool = False
    response_task: asyncio.Task | None = None
    pending_texts: list[str] = field(default_factory=list)

    @property
    def read_delay(self) -> float:
        """Short delay if the previous read already fired, otherwise a human-like delay."""
        return random.uniform(0.5, 2.0) if self.read_done else random.uniform(2, 20)

    @property
    def combined_text(self) -> str:
        """All accumulated message texts joined as a single input."""
        return "\n\n".join(self.pending_texts)

    def schedule_read(self, coro) -> None:
        """Cancel any stale read task and start a fresh one."""
        if self.read_task and not self.read_task.done():
            self.read_task.cancel()
        self.read_done = False
        self.read_task = asyncio.create_task(coro)

    async def schedule_response(self, coro, on_success: Callable[[asyncio.Task], None]) -> None:
        """Cancel any in-progress response task and start a new one."""
        if self.response_task and not self.response_task.done():
            self.response_task.cancel()
            try:
                await self.response_task
            except asyncio.CancelledError:
                pass
        self.response_task = asyncio.create_task(coro)
        self.response_task.add_done_callback(on_success)
