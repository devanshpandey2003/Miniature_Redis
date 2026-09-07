"""
Append-Only File (AOF) persistence --Idea: every mutating command gets
written as one JSON line to a log file *before* (or right after) it's
applied. On startup, replay the whole log to rebuild state.

This is intentionally simple (no compaction, no fsync tuning)
"""

import json
import asyncio
from pathlib import Path


class AOFLogger:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Prevents two concurrent requests from interleaving partial writes
        # to the log file.
        self._write_lock = asyncio.Lock()

    async def append(self, command: str, *args) -> None:
        """Log one mutating command. Called right after it succeeds."""
        line = json.dumps({"cmd": command, "args": args})
        async with self._write_lock:
            # Plain blocking file I/O is fine here: appends are small and
            # infrequent relative to request handling. For very high
            # throughput you'd move this to a thread via asyncio.to_thread.
            with open(self.path, "a") as f:
                f.write(line + "\n")

    async def replay(self, store) -> int:
        """
        Rebuild `store`'s state by replaying every logged command in order.
        Called once at application startup. Returns how many commands were
        replayed.
        """
        if not self.path.exists():
            return 0

        count = 0
        with open(self.path) as f:
            for raw_line in f:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                entry = json.loads(raw_line)
                cmd, args = entry["cmd"], entry["args"]

                if cmd == "SET":
                    key, value = args
                    await store.set(key, value)
                elif cmd == "DELETE":
                    await store.delete(args[0])
                elif cmd == "FLUSH":
                    await store.flush()
                elif cmd == "INCR":
                    key, amount = args
                    await store.incr(key, amount)
                # Unknown commands are skipped rather than crashing replay --
                # keeps old logs forward-compatible-ish.
                count += 1
        return count

    def clear(self) -> None:
        """Wipe the log -- call this after a fresh snapshot/flush if you add one."""
        if self.path.exists():
            self.path.unlink()
