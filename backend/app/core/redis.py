"""
Redis 7 In-Memory Layer, Standardized 6-Key Schema & Pub/Sub Utilities.
Complies with Chapter 3 & Chapter 4 of docs/SYSTEM_DESIGN.md.
"""
from __future__ import annotations

import asyncio
import fnmatch
import json
import logging
import time
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID

try:
    import redis.asyncio as aioredis
except ImportError:  # pragma: no cover
    aioredis = None

from app.core.config import settings

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. STANDARDIZED 6 REDIS KEY SCHEMAS & PUB/SUB CHANNEL (Chapter 3 & 4)
# ==============================================================================
TTL_QR_PIN_SECONDS = 60               # Key 1: qr:pin:{pin_code} (EX 60)
TTL_SESSION_ENROLLED_SECONDS = 7200   # Key 2: session:{session_id}:enrolled (EX 7200)
TTL_SESSION_MARKED_SECONDS = 7200     # Key 3: session:{session_id}:marked (EX 7200)
TTL_SESSION_DEVICE_SECONDS = 7200     # Key 4: session:{session_id}:device:{fp} (NX EX 7200)
TTL_COURSE_QUICKLOOK_SECONDS = 3600   # Key 5: course:{course_id}:quicklook (EX 3600)
TTL_RATELIMIT_PIN_SECONDS = 60        # Key 6: ratelimit:pin:{client_ip} (EX 60)
MAX_PIN_FAILURES_PER_MINUTE = 10      # EX-13: > 10 attempts/min -> HTTP 429


def key_qr_pin(pin_code: str) -> str:
    """Key 1 (STRING JSON, EX 60): Active 6-digit PIN metadata + Building GPS + Ultrasonic Freq."""
    return f"qr:pin:{pin_code.strip()}"


def key_session_enrolled(session_id: Union[str, UUID]) -> str:
    """Key 2 (HASH, EX 7200): student_code -> JSON {student_id, full_name, date_of_birth, admin_class}."""
    return f"session:{session_id}:enrolled"


def key_session_marked(session_id: Union[str, UUID]) -> str:
    """Key 3 (SET, EX 7200): Set of student_id strings already ATTENDED or PENDING_APPROVAL."""
    return f"session:{session_id}:marked"


def key_session_device(session_id: Union[str, UUID], device_fingerprint: str) -> str:
    """Key 4 (STRING, NX EX 7200): Anti-Proxy Device Lock storing first student_code using fp."""
    return f"session:{session_id}:device:{device_fingerprint.strip()}"


def key_course_quicklook(course_id: Union[str, UUID]) -> str:
    """Key 5 (STRING JSON, EX 3600): Cached Quick Look Preview matrix (< 1ms response)."""
    return f"course:{course_id}:quicklook"


def key_ratelimit_pin(client_ip: str) -> str:
    """Key 6 (STRING Int, EX 60): Brute-force counter per IP for invalid PIN / 4-field mismatches."""
    return f"ratelimit:pin:{client_ip.strip()}"


def channel_ws_session(session_id: Union[str, UUID]) -> str:
    """Chapter 4 Pub/Sub Channel: Multi-container WebSocket synchronization."""
    return f"ws:session:{session_id}"


# ==============================================================================
# 2. IN-MEMORY REDIS FALLBACK (For Automated Tests & Offline Local Dev)
# ==============================================================================
class InMemoryPubSub:
    """Async Pub/Sub emulator for InMemoryRedisFallback."""

    def __init__(self, broker: "InMemoryRedisFallback") -> None:
        self._broker = broker
        self._channels: Set[str] = set()
        self._queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

    async def subscribe(self, *channels: str) -> None:
        for ch in channels:
            self._channels.add(ch)
            self._broker._subscribers.setdefault(ch, set()).add(self._queue)

    async def unsubscribe(self, *channels: str) -> None:
        targets = channels if channels else tuple(self._channels)
        for ch in targets:
            self._channels.discard(ch)
            if ch in self._broker._subscribers:
                self._broker._subscribers[ch].discard(self._queue)

    async def get_message(
        self, ignore_subscribe_messages: bool = True, timeout: float = 1.0
    ) -> Optional[Dict[str, Any]]:
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def close(self) -> None:
        await self.unsubscribe()

    async def aclose(self) -> None:
        await self.close()


class InMemoryRedisFallback:
    """
    Thread/Async-safe in-memory Redis 7 compatible store with monotonic TTL expiration.
    Ensures 100% deterministic behavior in Pytest and environments where Redis daemon is offline.
    """

    def __init__(self) -> None:
        self._strings: Dict[str, str] = {}
        self._hashes: Dict[str, Dict[str, str]] = {}
        self._sets: Dict[str, Set[str]] = {}
        self._expiries: Dict[str, float] = {}
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}

    def _purge_if_expired(self, key: str) -> bool:
        exp = self._expiries.get(key)
        if exp is not None and time.monotonic() >= exp:
            self._strings.pop(key, None)
            self._hashes.pop(key, None)
            self._sets.pop(key, None)
            self._expiries.pop(key, None)
            return True
        return False

    def _exists(self, key: str) -> bool:
        self._purge_if_expired(key)
        return key in self._strings or key in self._hashes or key in self._sets

    async def ping(self) -> bool:
        return True

    async def get(self, key: str) -> Optional[str]:
        self._purge_if_expired(key)
        return self._strings.get(key)

    async def set(
        self,
        key: str,
        value: Union[str, int, float],
        ex: Optional[int] = None,
        nx: bool = False,
    ) -> Optional[bool]:
        self._purge_if_expired(key)
        if nx and self._exists(key):
            return None
        self._strings[key] = str(value)
        if ex is not None:
            self._expiries[key] = time.monotonic() + ex
        else:
            self._expiries.pop(key, None)
        return True

    async def setex(self, key: str, time_sec: int, value: Union[str, int, float]) -> bool:
        await self.set(key, value, ex=time_sec)
        return True

    async def delete(self, *keys: str) -> int:
        deleted = 0
        for k in keys:
            self._purge_if_expired(k)
            removed = False
            if k in self._strings:
                del self._strings[k]
                removed = True
            if k in self._hashes:
                del self._hashes[k]
                removed = True
            if k in self._sets:
                del self._sets[k]
                removed = True
            self._expiries.pop(k, None)
            if removed:
                deleted += 1
        return deleted

    async def exists(self, *keys: str) -> int:
        return sum(1 for k in keys if self._exists(k))

    async def expire(self, key: str, seconds: int) -> bool:
        if not self._exists(key):
            return False
        self._expiries[key] = time.monotonic() + seconds
        return True

    async def ttl(self, key: str) -> int:
        if not self._exists(key):
            return -2
        exp = self._expiries.get(key)
        if exp is None:
            return -1
        return max(0, int(round(exp - time.monotonic())))

    async def incr(self, key: str) -> int:
        self._purge_if_expired(key)
        current = int(self._strings.get(key, "0")) + 1
        self._strings[key] = str(current)
        return current

    # --- HASH Operations (Key 2: session:{session_id}:enrolled) ---
    async def hset(
        self,
        name: str,
        key: Optional[str] = None,
        value: Optional[str] = None,
        mapping: Optional[Dict[str, str]] = None,
    ) -> int:
        self._purge_if_expired(name)
        bucket = self._hashes.setdefault(name, {})
        added = 0
        if key is not None and value is not None:
            if key not in bucket:
                added += 1
            bucket[str(key)] = str(value)
        if mapping:
            for k, v in mapping.items():
                if str(k) not in bucket:
                    added += 1
                bucket[str(k)] = str(v)
        return added

    async def hget(self, name: str, key: str) -> Optional[str]:
        self._purge_if_expired(name)
        return self._hashes.get(name, {}).get(str(key))

    async def hgetall(self, name: str) -> Dict[str, str]:
        self._purge_if_expired(name)
        return dict(self._hashes.get(name, {}))

    # --- SET Operations (Key 3: session:{session_id}:marked) ---
    async def sadd(self, name: str, *values: Union[str, UUID]) -> int:
        self._purge_if_expired(name)
        bucket = self._sets.setdefault(name, set())
        added = 0
        for v in values:
            sv = str(v)
            if sv not in bucket:
                bucket.add(sv)
                added += 1
        return added

    async def srem(self, name: str, *values: Union[str, UUID]) -> int:
        self._purge_if_expired(name)
        bucket = self._sets.get(name)
        if not bucket:
            return 0
        removed = 0
        for v in values:
            sv = str(v)
            if sv in bucket:
                bucket.remove(sv)
                removed += 1
        return removed

    async def sismember(self, name: str, value: Union[str, UUID]) -> bool:
        self._purge_if_expired(name)
        return str(value) in self._sets.get(name, set())

    async def smembers(self, name: str) -> Set[str]:
        self._purge_if_expired(name)
        return set(self._sets.get(name, set()))

    async def keys(self, pattern: str = "*") -> List[str]:
        all_keys = set(self._strings.keys()) | set(self._hashes.keys()) | set(self._sets.keys())
        valid_keys = [k for k in all_keys if not self._purge_if_expired(k)]
        return [k for k in valid_keys if fnmatch.fnmatch(k, pattern)]

    async def flushall(self) -> bool:
        self._strings.clear()
        self._hashes.clear()
        self._sets.clear()
        self._expiries.clear()
        return True

    # --- PUB/SUB Operations (Chapter 4: ws:session:{session_id}) ---
    async def publish(self, channel: str, message: str) -> int:
        queues = list(self._subscribers.get(channel, set()))
        payload = {"type": "message", "channel": channel, "data": message}
        for q in queues:
            await q.put(payload)
        return len(queues)

    def pubsub(self) -> InMemoryPubSub:
        return InMemoryPubSub(self)

    async def close(self) -> None:
        pass

    async def aclose(self) -> None:
        pass


# ==============================================================================
# 3. CONNECTION MANAGEMENT & HIGH-LEVEL STATELESS GUARD HELPERS
# ==============================================================================
_redis_client: Optional[Any] = None
_fallback_client = InMemoryRedisFallback()
_using_fallback: bool = False


async def get_redis() -> Any:
    """
    Returns an active async Redis client.
    Automatically falls back to InMemoryRedisFallback if the Redis daemon is unreachable
    (e.g., during local unit testing without Docker).
    """
    global _redis_client, _using_fallback
    if _using_fallback:
        return _fallback_client

    if _redis_client is None and aioredis is not None:
        try:
            candidate = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=1.5,
                socket_timeout=1.5,
            )
            await candidate.ping()
            _redis_client = candidate
            logger.info("Connected to Redis 7 at %s", settings.REDIS_URL)
        except Exception as exc:
            logger.warning(
                "Redis server at %s unavailable (%s); activating InMemoryRedisFallback.",
                settings.REDIS_URL,
                exc,
            )
            _using_fallback = True
            return _fallback_client

    return _redis_client or _fallback_client


async def close_redis() -> None:
    """Gracefully closes the Redis connection pool on application shutdown."""
    global _redis_client
    if _redis_client is not None:
        try:
            if hasattr(_redis_client, "aclose"):
                await _redis_client.aclose()
            else:
                await _redis_client.close()
        except Exception:
            pass
        finally:
            _redis_client = None


# --- Helper 1: QR PIN 60s Cache (qr:pin:{pin_code}) ---
async def cache_qr_pin(pin_code: str, payload: Dict[str, Any], ttl: int = TTL_QR_PIN_SECONDS) -> None:
    r = await get_redis()
    await r.set(key_qr_pin(pin_code), json.dumps(payload), ex=ttl)


async def get_cached_qr_pin(pin_code: str) -> Optional[Dict[str, Any]]:
    r = await get_redis()
    raw = await r.get(key_qr_pin(pin_code))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def delete_qr_pin(pin_code: str) -> None:
    r = await get_redis()
    await r.delete(key_qr_pin(pin_code))


# --- Helper 2: Session Enrolled Roster Hash (session:{session_id}:enrolled) ---
async def cache_session_enrolled(
    session_id: Union[str, UUID],
    students_map: Dict[str, Dict[str, Any]],
    ttl: int = TTL_SESSION_ENROLLED_SECONDS,
) -> None:
    r = await get_redis()
    k = key_session_enrolled(session_id)
    await r.delete(k)
    if students_map:
        serialized = {code: json.dumps(info) for code, info in students_map.items()}
        await r.hset(k, mapping=serialized)
        await r.expire(k, ttl)


async def get_enrolled_student(
    session_id: Union[str, UUID], student_code: str
) -> Optional[Dict[str, Any]]:
    r = await get_redis()
    raw = await r.hget(key_session_enrolled(session_id), student_code.strip())
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


# --- Helper 3: Atomic Attendance Set (session:{session_id}:marked) ---
async def is_student_marked(session_id: Union[str, UUID], student_id: Union[str, UUID]) -> bool:
    r = await get_redis()
    return bool(await r.sismember(key_session_marked(session_id), str(student_id)))


async def mark_student_atomic(
    session_id: Union[str, UUID],
    student_id: Union[str, UUID],
    ttl: int = TTL_SESSION_MARKED_SECONDS,
) -> bool:
    """
    Atomically adds student_id to session:{session_id}:marked using SADD.
    Returns True if newly added, False if already present (prevents double-submit EX-05).
    """
    r = await get_redis()
    k = key_session_marked(session_id)
    added = await r.sadd(k, str(student_id))
    await r.expire(k, ttl)
    return int(added) == 1


async def unmark_student(session_id: Union[str, UUID], student_id: Union[str, UUID]) -> None:
    r = await get_redis()
    await r.srem(key_session_marked(session_id), str(student_id))


# --- Helper 4: Anti-Proxy Device Lock (session:{session_id}:device:{fp}) ---
async def check_and_lock_device(
    session_id: Union[str, UUID],
    device_fingerprint: Optional[str],
    student_code: str,
    ttl: int = TTL_SESSION_DEVICE_SECONDS,
) -> Optional[str]:
    """
    Enforces BR-16 / EX-12 (Anti-Proxy Device Lock):
    - If device_fingerprint is empty/None, returns None (allowed).
    - Uses SET NX EX 7200 to bind the device to the first student_code.
    - Returns None if allowed (either newly bound or bound to the SAME student_code).
    - Returns the existing owner's student_code if bound to a DIFFERENT student.
    """
    if not device_fingerprint or not device_fingerprint.strip():
        return None
    r = await get_redis()
    k = key_session_device(session_id, device_fingerprint)
    code_clean = student_code.strip()
    was_set = await r.set(k, code_clean, ex=ttl, nx=True)
    if was_set:
        return None
    owner = await r.get(k)
    if owner and owner != code_clean:
        return owner
    return None


# --- Helper 5: Course QuickLook Cache (course:{course_id}:quicklook) ---
async def get_cached_quicklook(course_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
    r = await get_redis()
    raw = await r.get(key_course_quicklook(course_id))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def set_cached_quicklook(
    course_id: Union[str, UUID],
    data: Dict[str, Any],
    ttl: int = TTL_COURSE_QUICKLOOK_SECONDS,
) -> None:
    r = await get_redis()
    await r.set(key_course_quicklook(course_id), json.dumps(data), ex=ttl)


async def invalidate_course_quicklook(course_id: Union[str, UUID]) -> None:
    r = await get_redis()
    await r.delete(key_course_quicklook(course_id))


# --- Helper 6: Brute-Force Rate Limiting (ratelimit:pin:{client_ip}) ---
async def get_pin_failures(client_ip: str) -> int:
    r = await get_redis()
    val = await r.get(key_ratelimit_pin(client_ip))
    return int(val) if val and str(val).isdigit() else 0


async def increment_pin_failure(
    client_ip: str, ttl: int = TTL_RATELIMIT_PIN_SECONDS
) -> int:
    r = await get_redis()
    k = key_ratelimit_pin(client_ip)
    count = await r.incr(k)
    if count == 1:
        await r.expire(k, ttl)
    return int(count)


async def clear_session_redis_state(
    session_id: Union[str, UUID], pin_codes: Optional[List[str]] = None
) -> None:
    """
    Cleans up all Redis keys associated with a session when closed or reset (UC12 / UC13).
    """
    r = await get_redis()
    keys_to_delete = [
        key_session_enrolled(session_id),
        key_session_marked(session_id),
    ]
    if pin_codes:
        keys_to_delete.extend(key_qr_pin(p) for p in pin_codes if p)
    device_keys = await r.keys(f"session:{session_id}:device:*")
    if device_keys:
        keys_to_delete.extend(device_keys)
    if keys_to_delete:
        await r.delete(*keys_to_delete)
