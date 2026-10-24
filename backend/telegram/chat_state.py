import asyncio
import random
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PendingMessage:
    """An incoming message that has not been answered yet."""
    message_id: int
    text: str


@dataclass
class ChatState:
    """Coalescing state for a single chat."""
    read_task: asyncio.Task | None = None
    read_done: bool = False
    response_task: asyncio.Task | None = None
    # send + store of a generated reply; never cancelled so a sent reply is always recorded
    commit_task: asyncio.Task | None = None
    pending: list[PendingMessage] = field(default_factory=list)

    @property
    def read_delay(self) -> float:
        """Short delay if the previous read already fired, otherwise a human-like delay."""
        return random.uniform(0.5, 2.0) if self.read_done else random.uniform(2, 20)

    def add_pending(self, message_id: int, text: str) -> None:
        self.pending.append(PendingMessage(message_id, text))

    def mark_answered(self, answered: list[PendingMessage]) -> None:
        """Drop *answered* from the pending list, keeping anything that arrived since."""
        self.pending = [p for p in self.pending if p not in answered]

    def schedule_read(self, coro) -> None:
        """Cancel any stale read task and start a fresh one."""
        if self.read_task and not self.read_task.done():
            self.read_task.cancel()
        self.read_done = False
        self.read_task = asyncio.create_task(coro)

    async def wait_for_read(self) -> None:
        """Wait until the latest read task has finished, even if earlier ones were superseded."""
        while self.read_task and not self.read_task.done():
            await asyncio.wait({self.read_task})

    async def wait_for_commit(self) -> None:
        """Wait for an in-flight send + store without cancelling it if we get cancelled."""
        if self.commit_task and not self.commit_task.done():
            await asyncio.shield(self.commit_task)

    async def cancel_response(self) -> None:
        """Cancel any in-progress response task and wait for it to finish."""
        if self.response_task and not self.response_task.done():
            self.response_task.cancel()
            try:
                await self.response_task
            except asyncio.CancelledError:
                pass

    async def schedule_response(self, coro) -> None:
        """Cancel any in-progress response task and start a new one."""
        await self.cancel_response()
        self.response_task = asyncio.create_task(coro)
