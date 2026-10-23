import asyncio
import time
from typing import Any, Callable, Dict, Optional
import structlog
from fastapi import Depends, Header, Request

from config import settings
from auth_utils import get_current_active_user, UserResponse

logger = structlog.get_logger(__name__)


class SessionContainer:
    """Holds scoped calculation engine instances and session metadata."""

    def __init__(self, session_key: str):
        self.session_key: str = session_key
        self.created_at: float = time.time()
        self.last_accessed: float = time.time()
        self.engines: Dict[str, Any] = {}

    def touch(self) -> None:
        """Updates last accessed timestamp for LRU / TTL tracking."""
        self.last_accessed = time.time()

    def is_expired(self, ttl_seconds: float) -> bool:
        """Checks if session has expired based on TTL."""
        return (time.time() - self.last_accessed) > ttl_seconds


class SessionRegistry:
    """
    User/Session-scoped resource manager that isolates calculation engine instances.
    Provides thread/async-safe concurrency locking, LRU capacity management,
    and automatic background TTL eviction.
    """

    def __init__(
        self,
        default_ttl: int = 3600,
        max_capacity: int = 100,
        cleanup_interval: int = 300,
    ):
        self._sessions: Dict[str, SessionContainer] = {}
        self._lock = asyncio.Lock()
        self.default_ttl = default_ttl
        self.max_capacity = max_capacity
        self.cleanup_interval = cleanup_interval
        self._janitor_task: Optional[asyncio.Task] = None

    async def get_or_create_engine(
        self, session_key: str, engine_type: str, factory_fn: Callable[[], Any]
    ) -> Any:
        """Retrieves or instantiates an engine for a given session key."""
        async with self._lock:
            container = self._sessions.get(session_key)
            if container is None:
                if len(self._sessions) >= self.max_capacity:
                    self._evict_lru_unlocked()

                container = SessionContainer(session_key)
                self._sessions[session_key] = container

            container.touch()
            if engine_type not in container.engines:
                container.engines[engine_type] = factory_fn()

            return container.engines[engine_type]

    async def reset_engine(self, session_key: str, engine_type: str) -> None:
        """Removes a specific engine instance for a session key."""
        async with self._lock:
            container = self._sessions.get(session_key)
            if container and engine_type in container.engines:
                del container.engines[engine_type]

    async def clear_all(self) -> None:
        """Clears all registered sessions."""
        async with self._lock:
            self._sessions.clear()

    def _evict_lru_unlocked(self) -> None:
        """Evicts least recently used session. Must be called with self._lock held."""
        if not self._sessions:
            return
        lru_key = min(
            self._sessions.keys(),
            key=lambda k: self._sessions[k].last_accessed,
        )
        del self._sessions[lru_key]
        logger.info(f"SessionRegistry evicted LRU session: {lru_key}")

    async def start_janitor_task(self) -> None:
        """Starts background task to periodically purge expired sessions."""
        if self._janitor_task is None or self._janitor_task.done():
            self._janitor_task = asyncio.create_task(self._janitor_loop())

    async def stop_janitor_task(self) -> None:
        """Stops background janitor task."""
        if self._janitor_task and not self._janitor_task.done():
            self._janitor_task.cancel()
            await asyncio.gather(self._janitor_task, return_exceptions=True)
            self._janitor_task = None

    async def _janitor_loop(self) -> None:
        """Periodic background loop checking for expired sessions."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                async with self._lock:
                    now = time.time()
                    expired_keys = [
                        key
                        for key, container in self._sessions.items()
                        if (now - container.last_accessed) > self.default_ttl
                    ]
                    for key in expired_keys:
                        del self._sessions[key]
                    if expired_keys:
                        logger.info(
                            f"Janitor purged {len(expired_keys)} expired sessions."
                        )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"Error in SessionRegistry janitor loop: {e}", exc_info=True
                )


def get_legacy_global_singleton(engine_name: str) -> Any:
    """Fallback helper to return global engine singletons when USE_SESSION_REGISTRY is False."""
    import main  # Lazy import to avoid circular dependency

    if engine_name == "ai_predictor":
        return getattr(main, "ai_predictor", None)
    return getattr(main, engine_name, None)


async def get_engine_instance(
    engine_name: str,
    factory_fn: Callable[[], Any],
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user),
    session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> Any:
    """FastAPI dependency helper to retrieve session-scoped or fallback global engines."""
    if not settings.USE_SESSION_REGISTRY:
        return get_legacy_global_singleton(engine_name)

    registry: SessionRegistry = getattr(request.app.state, "session_registry", None)
    if registry is None:
        # Fallback if app.state.session_registry was not set
        return get_legacy_global_singleton(engine_name)

    session_key = (
        f"{current_user.id}:{session_id}" if session_id else str(current_user.id)
    )

    return await registry.get_or_create_engine(
        session_key=session_key,
        engine_type=engine_name,
        factory_fn=factory_fn,
    )
