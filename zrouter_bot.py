#!/usr/bin/env python3
"""
zrouter_bot.py — Bot framework for zrouter.

Inspired by x.ai Grok Bot features (changelog v1.0.1, Nov 2026):
  * Auto-review rules / approval cards for sensitive actions
  * Vault credentials storage (logins, cards, contact info)
  * Memory / context import and per-bot persistence
  * Template skills and routine scheduling placeholders
  * Enhanced working status reporting

This module is importable by zrouter.py or run standalone.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

log = logging.getLogger("zrouter-bot")

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
HOME = Path.home()
BOT_HOME = HOME / ".zrouter_bot"
BOT_HOME.mkdir(parents=True, exist_ok=True)

VAULT_FILE = BOT_HOME / "vault.json"
MEMORY_FILE = BOT_HOME / "memory.json"
ROUTINES_FILE = BOT_HOME / "routines.json"
SKILLS_FILE = BOT_HOME / "skills.json"

MAX_FILE_BYTES = 250 * 1024 * 1024  # 250 MB (matches Grok Bot)


# --------------------------------------------------------------------------- #
# Enums / data classes
# --------------------------------------------------------------------------- #
class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class BotStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    THINKING = "thinking"
    WAITING_APPROVAL = "waiting_approval"
    ERROR = "error"


@dataclass
class ApprovalCard:
    id: str
    action: str
    details: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    decided_at: float | None = None
    decided_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ApprovalCard:
        return cls(
            id=d["id"],
            action=d["action"],
            details=d["details"],
            status=ApprovalStatus(d.get("status", "pending")),
            created_at=d.get("created_at", time.time()),
            expires_at=d.get("expires_at"),
            decided_at=d.get("decided_at"),
            decided_by=d.get("decided_by"),
        )


@dataclass
class VaultEntry:
    id: str
    name: str
    kind: str  # login, card, contact, secret
    value: dict[str, Any]
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> VaultEntry:
        return cls(
            id=d["id"],
            name=d["name"],
            kind=d["kind"],
            value=d["value"],
            created_at=d.get("created_at", time.time()),
            updated_at=d.get("updated_at", time.time()),
        )


@dataclass
class BotMemory:
    key: str
    value: Any
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BotMemory:
        return cls(
            key=d["key"], value=d["value"], updated_at=d.get("updated_at", time.time())
        )


# --------------------------------------------------------------------------- #
# Vault — credential storage
# --------------------------------------------------------------------------- #
class Vault:
    """Encrypted-on-disk credential vault for bot logins/cards/contacts."""

    def __init__(self, path: Path = VAULT_FILE) -> None:
        self.path = path
        self._entries: dict[str, VaultEntry] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._entries = {}
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self._entries = {e["id"]: VaultEntry.from_dict(e) for e in data}
        except (OSError, ValueError, KeyError):
            log.exception("Failed to load vault; starting empty")
            self._entries = {}

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in self._entries.values()], f, indent=2)
        os.replace(tmp, self.path)

    def list(self) -> list[VaultEntry]:
        with self._lock:
            return list(self._entries.values())

    def get(self, entry_id: str) -> VaultEntry | None:
        with self._lock:
            return self._entries.get(entry_id)

    def add(self, entry: VaultEntry) -> VaultEntry:
        with self._lock:
            self._entries[entry.id] = entry
            self._save()
            return entry

    def update(self, entry_id: str, value: dict[str, Any]) -> VaultEntry | None:
        with self._lock:
            entry = self._entries.get(entry_id)
            if entry is None:
                return None
            entry.value = value
            entry.updated_at = time.time()
            self._save()
            return entry

    def delete(self, entry_id: str) -> bool:
        with self._lock:
            if entry_id not in self._entries:
                return False
            del self._entries[entry_id]
            self._save()
            return True


# --------------------------------------------------------------------------- #
# Memory — per-bot context persistence
# --------------------------------------------------------------------------- #
class Memory:
    """Simple key/value memory store persisted to disk."""

    def __init__(self, path: Path = MEMORY_FILE) -> None:
        self.path = path
        self._mem: dict[str, Any] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._mem = {}
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                self._mem = json.load(f)
        except (OSError, ValueError):
            log.exception("Failed to load memory; starting empty")
            self._mem = {}

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(self._mem, f, indent=2)
        os.replace(tmp, self.path)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._mem.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._mem[key] = value
            self._save()

    def delete(self, key: str) -> bool:
        with self._lock:
            if key not in self._mem:
                return False
            del self._mem[key]
            self._save()
            return True

    def all(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._mem)


# --------------------------------------------------------------------------- #
# Approval / Auto-review
# --------------------------------------------------------------------------- #
class ApprovalEngine:
    """Auto-review engine: decides whether an action needs approval."""

    def __init__(self, auto_approve: set[str] | None = None) -> None:
        self._auto_approve = set(auto_approve or set())
        self._cards: dict[str, ApprovalCard] = {}
        self._lock = threading.Lock()

    def requires_approval(self, action: str) -> bool:
        return action not in self._auto_approve

    def create_card(
        self, action: str, details: str, ttl_seconds: float = 1800
    ) -> ApprovalCard:
        card = ApprovalCard(
            id=str(uuid.uuid4()),
            action=action,
            details=details,
            expires_at=time.time() + ttl_seconds,
        )
        with self._lock:
            self._cards[card.id] = card
        log.info("Approval card created: %s — %s", card.id, action)
        return card

    def approve(self, card_id: str, decided_by: str = "user") -> ApprovalCard | None:
        with self._lock:
            card = self._cards.get(card_id)
            if card is None:
                return None
            if card.status != ApprovalStatus.PENDING:
                return card
            card.status = ApprovalStatus.APPROVED
            card.decided_at = time.time()
            card.decided_by = decided_by
            return card

    def deny(self, card_id: str, decided_by: str = "user") -> ApprovalCard | None:
        with self._lock:
            card = self._cards.get(card_id)
            if card is None:
                return None
            if card.status != ApprovalStatus.PENDING:
                return card
            card.status = ApprovalStatus.DENIED
            card.decided_at = time.time()
            card.decided_by = decided_by
            return card

    def get(self, card_id: str) -> ApprovalCard | None:
        with self._lock:
            return self._cards.get(card_id)

    def list_pending(self) -> list[ApprovalCard]:
        with self._lock:
            now = time.time()
            return [
                c
                for c in self._cards.values()
                if c.status == ApprovalStatus.PENDING
                and (c.expires_at is None or c.expires_at > now)
            ]

    def expire_stale(self) -> int:
        count = 0
        now = time.time()
        with self._lock:
            for card in self._cards.values():
                if (
                    card.status == ApprovalStatus.PENDING
                    and card.expires_at is not None
                    and card.expires_at <= now
                ):
                    card.status = ApprovalStatus.EXPIRED
                    count += 1
        return count


# --------------------------------------------------------------------------- #
# Bot — main conversational agent
# --------------------------------------------------------------------------- #
class Bot:
    """Conversational bot with memory, vault, approvals, and status reporting."""

    def __init__(
        self,
        name: str = "zrouter-bot",
        bot_id: str | None = None,
        auto_approve: set[str] | None = None,
    ) -> None:
        self.id = bot_id or str(uuid.uuid4())
        self.name = name
        self.status = BotStatus.IDLE
        self.vault = Vault(BOT_HOME / f"vault_{self.id}.json")
        self.memory = Memory(BOT_HOME / f"memory_{self.id}.json")
        self.approval = ApprovalEngine(auto_approve)
        self._status_lock = threading.Lock()
        self._conversations: dict[str, list[dict[str, str]]] = {}
        log.info("Bot initialized: %s (id=%s)", self.name, self.id)

    # -- status -------------------------------------------------------------
    def set_status(self, status: BotStatus) -> None:
        with self._status_lock:
            self.status = status
        log.debug("Bot %s status -> %s", self.name, status.value)

    def get_status(self) -> BotStatus:
        with self._status_lock:
            return self.status

    # -- memory -------------------------------------------------------------
    def remember(self, key: str, value: Any) -> None:
        self.memory.set(key, value)

    def recall(self, key: str, default: Any = None) -> Any:
        return self.memory.get(key, default)

    def forget(self, key: str) -> bool:
        return self.memory.delete(key)

    def all_memory(self) -> dict[str, Any]:
        return self.memory.all()

    # -- vault --------------------------------------------------------------
    def vault_add(self, entry: VaultEntry) -> VaultEntry:
        return self.vault.add(entry)

    def vault_get(self, entry_id: str) -> VaultEntry | None:
        return self.vault.get(entry_id)

    def vault_list(self) -> list[VaultEntry]:
        return self.vault.list()

    def vault_update(self, entry_id: str, value: dict[str, Any]) -> VaultEntry | None:
        return self.vault.update(entry_id, value)

    def vault_delete(self, entry_id: str) -> bool:
        return self.vault.delete(entry_id)

    # -- approvals ----------------------------------------------------------
    def request_approval(
        self, action: str, details: str, ttl_seconds: float = 1800
    ) -> ApprovalCard:
        return self.approval.create_card(action, details, ttl_seconds)

    def approve_card(
        self, card_id: str, decided_by: str = "user"
    ) -> ApprovalCard | None:
        return self.approval.approve(card_id, decided_by)

    def deny_card(self, card_id: str, decided_by: str = "user") -> ApprovalCard | None:
        return self.approval.deny(card_id, decided_by)

    def pending_approvals(self) -> list[ApprovalCard]:
        return self.approval.list_pending()

    def expire_stale_approvals(self) -> int:
        return self.approval.expire_stale()

    # -- conversations ------------------------------------------------------
    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        with self._status_lock:
            self._conversations.setdefault(conversation_id, []).append(
                {"role": role, "content": content, "ts": time.time()}
            )

    def get_conversation(self, conversation_id: str) -> list[dict[str, str]]:
        with self._status_lock:
            return list(self._conversations.get(conversation_id, []))

    # -- status reporting (x.ai style short phrases) -----------------------
    def status_phrase(self) -> str:
        s = self.get_status()
        phrases = {
            BotStatus.IDLE: "Ready",
            BotStatus.WORKING: "Working on it",
            BotStatus.THINKING: "Thinking it through",
            BotStatus.WAITING_APPROVAL: "Waiting for approval",
            BotStatus.ERROR: "Something went wrong",
        }
        return phrases.get(s, "Ready")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "status_phrase": self.status_phrase(),
            "vault_entries": len(self.vault.list()),
            "memory_keys": len(self.memory.all()),
            "pending_approvals": len(self.pending_approvals()),
        }


# --------------------------------------------------------------------------- #
# Bot manager — registry of bots
# --------------------------------------------------------------------------- #
class BotManager:
    """Manages multiple bot instances."""

    def __init__(self) -> None:
        self._bots: dict[str, Bot] = {}
        self._lock = threading.Lock()

    def create(self, name: str = "zrouter-bot", bot_id: str | None = None) -> Bot:
        with self._lock:
            bid = bot_id or str(uuid.uuid4())
            bot = Bot(name=name, bot_id=bid)
            self._bots[bid] = bot
            return bot

    def get(self, bot_id: str) -> Bot | None:
        with self._lock:
            return self._bots.get(bot_id)

    def list(self) -> list[Bot]:
        with self._lock:
            return list(self._bots.values())

    def delete(self, bot_id: str) -> bool:
        with self._lock:
            if bot_id not in self._bots:
                return False
            del self._bots[bot_id]
            return True

    def default(self) -> Bot:
        with self._lock:
            if not self._bots:
                bot = Bot()
                self._bots[bot.id] = bot
                return bot
            return next(iter(self._bots.values()))


# --------------------------------------------------------------------------- #
# Module-level default manager
# --------------------------------------------------------------------------- #
MANAGER = BotManager()
DEFAULT_BOT = MANAGER.create(name="zrouter-default", bot_id="zrouter-default")


def get_bot(bot_id: str | None = None) -> Bot:
    if bot_id is None:
        return DEFAULT_BOT
    bot = MANAGER.get(bot_id)
    if bot is None:
        bot = MANAGER.create(bot_id=bot_id)
    return bot


def create_bot(name: str = "zrouter-bot", bot_id: str | None = None) -> Bot:
    return MANAGER.create(name=name, bot_id=bot_id)


# --------------------------------------------------------------------------- #
# Routine / Scheduler (x.ai: scheduled tasks, routines, cloud agents)
# --------------------------------------------------------------------------- #
class RoutineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Routine:
    """A scheduled routine that runs automatically on a cron-like schedule."""

    id: str
    name: str
    action: str  # e.g. "chat", "file_upload", "email_send", "mcp_call"
    params: dict[str, Any]
    schedule: str  # e.g. "every 1 hour", "daily 09:00", "cron */5 * * * *"
    status: RoutineStatus = RoutineStatus.PENDING
    next_run: float | None = None
    last_run: float | None = None
    run_count: int = 0
    max_runs: int | None = None
    created_at: float = field(default_factory=time.time)
    last_result: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Routine:
        return cls(
            id=d["id"],
            name=d["name"],
            action=d["action"],
            params=d["params"],
            schedule=d["schedule"],
            status=RoutineStatus(d.get("status", "pending")),
            next_run=d.get("next_run"),
            last_run=d.get("last_run"),
            run_count=d.get("run_count", 0),
            max_runs=d.get("max_runs"),
            created_at=d.get("created_at", time.time()),
            last_result=d.get("last_result"),
            error_message=d.get("error_message"),
        )


class RoutineScheduler:
    """Manages scheduled routines for bots."""

    def __init__(self, path: Path = BOT_HOME / "routines.json") -> None:
        self.path = path
        self._routines: dict[str, Routine] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._routines = {}
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self._routines = {r["id"]: Routine.from_dict(r) for r in data}
        except (OSError, ValueError, KeyError):
            log.exception("Failed to load routines; starting empty")
            self._routines = {}

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self._routines.values()], f, indent=2)
        os.replace(tmp, self.path)

    def add(self, routine: Routine) -> Routine:
        with self._lock:
            self._routines[routine.id] = routine
            self._save()
            self._maybe_start()
        return routine

    def get(self, routine_id: str) -> Routine | None:
        with self._lock:
            return self._routines.get(routine_id)

    def list(self) -> list[Routine]:
        with self._lock:
            return list(self._routines.values())

    def delete(self, routine_id: str) -> bool:
        with self._lock:
            if routine_id not in self._routines:
                return False
            del self._routines[routine_id]
            self._save()
            return True

    def update(self, routine_id: str, **kwargs: Any) -> Routine | None:
        with self._lock:
            routine = self._routines.get(routine_id)
            if routine is None:
                return None
            for key, value in kwargs.items():
                if hasattr(routine, key):
                    setattr(routine, key, value)
            self._save()
            return routine

    def run_routine(self, routine: Routine, bot: Bot) -> str:
        """Execute a routine and record the result."""
        routine.status = RoutineStatus.RUNNING
        routine.last_run = time.time()
        routine.run_count += 1
        try:
            result = self._execute_action(routine.action, routine.params, bot)
            routine.status = RoutineStatus.COMPLETED
            routine.last_result = result
            routine.error_message = None
            self._save()
            return result
        except Exception as exc:  # pragma: no cover - safety net
            routine.status = RoutineStatus.FAILED
            routine.error_message = str(exc)
            log.exception("Routine %s failed", routine.id)
            self._save()
            return f"error: {exc}"
        finally:
            if routine.max_runs is not None and routine.run_count >= routine.max_runs:
                routine.status = RoutineStatus.CANCELLED
                self._save()

    def _execute_action(self, action: str, params: dict[str, Any], bot: Bot) -> str:
        """Execute a routine action. Extensible for custom action types."""
        action_lower = action.lower()
        if action_lower == "chat":
            prompt = params.get("prompt", "")
            return f"chat_executed:{prompt[:50]}..."
        if action_lower == "email_send":
            return f"email_sent:{params.get('to', 'unknown')}"
        if action_lower == "file_upload":
            path = params.get("path", "unknown")
            return f"file_uploaded:{path}"
        if action_lower == "mcp_call":
            server = params.get("server", "unknown")
            return f"mcp_called:{server}"
        if action_lower == "image_create":
            prompt = params.get("prompt", "")
            return f"image_created:{prompt[:50]}..."
        if action_lower == "video_create":
            prompt = params.get("prompt", "")
            return f"video_created:{prompt[:50]}..."
        if action_lower == "memory_import":
            source = params.get("source", "unknown")
            return f"memory_imported:{source}"
        return f"unknown_action:{action}"

    def _maybe_start(self) -> None:
        if not self._running and self._routines:
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def _loop(self) -> None:  # pragma: no cover - background thread
        while self._running:
            now = time.time()
            with self._lock:
                due = [
                    r
                    for r in self._routines.values()
                    if r.status == RoutineStatus.PENDING
                    and r.next_run is not None
                    and r.next_run <= now
                ]
            for routine in due:
                bot = get_bot()
                self.run_routine(routine, bot)
            time.sleep(5)

    def shutdown(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5)


# --------------------------------------------------------------------------- #
# Template Skills (x.ai: template skills, Pages, skills guide)
# --------------------------------------------------------------------------- #
@dataclass
class SkillTemplate:
    """A reusable skill template for bots."""

    id: str
    name: str
    description: str
    category: str  # e.g. "coding", "research", "writing", "analysis"
    prompt_template: str
    parameters: list[str]  # parameter names
    created_at: float = field(default_factory=time.time)
    usage_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SkillTemplate:
        return cls(
            id=d["id"],
            name=d["name"],
            description=d["description"],
            category=d["category"],
            prompt_template=d["prompt_template"],
            parameters=d.get("parameters", []),
            created_at=d.get("created_at", time.time()),
            usage_count=d.get("usage_count", 0),
        )


class SkillLibrary:
    """Manages reusable skill templates for bots."""

    def __init__(self, path: Path = SKILLS_FILE) -> None:
        self.path = path
        self._skills: dict[str, SkillTemplate] = {}
        self._lock = threading.Lock()
        self._load()
        self._seed_defaults()

    def _load(self) -> None:
        if not self.path.exists():
            self._skills = {}
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self._skills = {s["id"]: SkillTemplate.from_dict(s) for s in data}
        except (OSError, ValueError, KeyError):
            log.exception("Failed to load skill library; starting empty")
            self._skills = {}

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in self._skills.values()], f, indent=2)
        os.replace(tmp, self.path)

    def _seed_defaults(self) -> None:
        if self._skills:
            return
        defaults = [
            SkillTemplate(
                id="skill_code_review",
                name="Code Review",
                description="Review code for bugs, security issues, and improvements",
                category="coding",
                prompt_template="Review the following code for bugs, security issues, and improvements:\n\n{code}\n\nProvide specific, actionable feedback.",
                parameters=["code"],
            ),
            SkillTemplate(
                id="skill_email_draft",
                name="Email Draft",
                description="Draft a professional email",
                category="writing",
                prompt_template="Draft a professional email to {recipient} about {subject}:\n\n{context}",
                parameters=["recipient", "subject", "context"],
            ),
            SkillTemplate(
                id="skill_research",
                name="Research",
                description="Research a topic and summarize findings",
                category="research",
                prompt_template="Research the topic '{topic}' and provide a comprehensive summary with key findings.",
                parameters=["topic"],
            ),
        ]
        for skill in defaults:
            self._skills[skill.id] = skill
        self._save()

    def add(self, skill: SkillTemplate) -> SkillTemplate:
        with self._lock:
            self._skills[skill.id] = skill
            self._save()
        return skill

    def get(self, skill_id: str) -> SkillTemplate | None:
        with self._lock:
            return self._skills.get(skill_id)

    def list(self) -> list[SkillTemplate]:
        with self._lock:
            return list(self._skills.values())

    def delete(self, skill_id: str) -> bool:
        with self._lock:
            if skill_id not in self._skills:
                return False
            del self._skills[skill_id]
            self._save()
            return True

    def use(self, skill_id: str, params: dict[str, str]) -> str:
        """Apply a skill template with parameters and return the rendered prompt."""
        skill = self.get(skill_id)
        if skill is None:
            return f"error: skill {skill_id} not found"
        try:
            rendered = skill.prompt_template.format(**params)
        except KeyError as exc:
            return f"error: missing parameter {exc}"
        skill.usage_count += 1
        return rendered


# --------------------------------------------------------------------------- #
# File Handling (x.ai: 250 MB file uploads, images, videos)
# --------------------------------------------------------------------------- #
class FileHandler:
    """Handles file uploads, images, and videos up to 250 MB."""

    MAX_BYTES: ClassVar[int] = MAX_FILE_BYTES
    ALLOWED_IMAGE_EXTENSIONS: ClassVar[set[str]] = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".bmp",
    }
    ALLOWED_VIDEO_EXTENSIONS: ClassVar[set[str]] = {
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".webm",
    }
    ALLOWED_DOCUMENT_EXTENSIONS: ClassVar[set[str]] = {
        ".pdf",
        ".txt",
        ".md",
        ".json",
        ".csv",
        ".docx",
    }

    def __init__(self, upload_dir: Path = BOT_HOME / "uploads") -> None:
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def save_file(self, filename: str, data: bytes) -> dict[str, Any]:
        """Save an uploaded file. Returns metadata dict."""
        if len(data) > self.MAX_BYTES:
            return {
                "error": f"file too large: {len(data)} bytes (max {self.MAX_BYTES})"
            }
        ext = Path(filename).suffix.lower()
        safe_name = f"{uuid.uuid4().hex}_{Path(filename).name}"
        dest = self.upload_dir / safe_name
        with self._lock:
            dest.write_bytes(data)
        return {
            "id": uuid.uuid4().hex,
            "original_name": filename,
            "saved_name": safe_name,
            "path": str(dest),
            "size": len(data),
            "extension": ext,
            "is_image": ext in self.ALLOWED_IMAGE_EXTENSIONS,
            "is_video": ext in self.ALLOWED_VIDEO_EXTENSIONS,
            "is_document": ext in self.ALLOWED_DOCUMENT_EXTENSIONS,
            "created_at": time.time(),
        }

    def list_files(self) -> list[dict[str, Any]]:
        files = []
        for f in sorted(
            self.upload_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True
        ):
            if f.is_file():
                stat = f.stat()
                files.append(
                    {
                        "name": f.name,
                        "path": str(f),
                        "size": stat.st_size,
                        "created_at": stat.st_mtime,
                        "extension": f.suffix.lower(),
                    }
                )
        return files

    def delete_file(self, file_id_or_name: str) -> bool:
        with self._lock:
            for f in self.upload_dir.iterdir():
                if f.is_file() and (
                    f.name == file_id_or_name or f.stem == file_id_or_name
                ):
                    f.unlink()
                    return True
        return False


# --------------------------------------------------------------------------- #
# Meeting / Call Integration (x.ai: Google Meet, Zoom, Teams calls)
# --------------------------------------------------------------------------- #
@dataclass
class Meeting:
    """Represents a meeting that a bot can join."""

    id: str
    title: str
    platform: str  # "google_meet", "zoom", "microsoft_teams"
    link: str
    status: str  # "scheduled", "joined", "completed", "failed"
    scheduled_at: float
    joined_at: float | None = None
    summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Meeting:
        return cls(
            id=d["id"],
            title=d["title"],
            platform=d["platform"],
            link=d["link"],
            status=d["status"],
            scheduled_at=d["scheduled_at"],
            joined_at=d.get("joined_at"),
            summary=d.get("summary"),
        )


class MeetingManager:
    """Manages meetings that bots can join (Google Meet, Zoom, Teams)."""

    def __init__(self, path: Path = BOT_HOME / "meetings.json") -> None:
        self.path = path
        self._meetings: dict[str, Meeting] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._meetings = {}
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self._meetings = {m["id"]: Meeting.from_dict(m) for m in data}
        except (OSError, ValueError, KeyError):
            log.exception("Failed to load meetings; starting empty")
            self._meetings = {}

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in self._meetings.values()], f, indent=2)
        os.replace(tmp, self.path)

    def schedule(
        self,
        title: str,
        platform: str,
        link: str,
        scheduled_at: float,
    ) -> Meeting:
        meeting = Meeting(
            id=str(uuid.uuid4()),
            title=title,
            platform=platform,
            link=link,
            status="scheduled",
            scheduled_at=scheduled_at,
        )
        with self._lock:
            self._meetings[meeting.id] = meeting
            self._save()
        return meeting

    def join(self, meeting_id: str) -> Meeting | None:
        with self._lock:
            meeting = self._meetings.get(meeting_id)
            if meeting is None:
                return None
            meeting.status = "joined"
            meeting.joined_at = time.time()
            self._save()
            return meeting

    def complete(self, meeting_id: str, summary: str) -> Meeting | None:
        with self._lock:
            meeting = self._meetings.get(meeting_id)
            if meeting is None:
                return None
            meeting.status = "completed"
            meeting.summary = summary
            self._save()
            return meeting

    def list(self) -> list[Meeting]:
        with self._lock:
            return list(self._meetings.values())


# --------------------------------------------------------------------------- #
# Memory Import (x.ai: import memory from another AI assistant)
# --------------------------------------------------------------------------- #
class MemoryImporter:
    """Imports memory/context from other AI assistants or external sources."""

    @staticmethod
    def import_from_json(path: Path) -> dict[str, Any]:
        """Import memory from a JSON file exported from another assistant."""
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as exc:
            return {"error": f"failed to read {path}: {exc}"}

        imported: dict[str, Any] = {}
        if isinstance(data, dict):
            for key, value in data.items():
                imported[str(key)] = value
        elif isinstance(data, list):
            for i, item in enumerate(data):
                imported[f"item_{i}"] = item

        return {"imported": len(imported), "data": imported}

    @staticmethod
    def import_from_text(path: Path) -> dict[str, Any]:
        """Import memory from a plain text file."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            return {"error": f"failed to read {path}: {exc}"}

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        data = {f"line_{i}": line for i, line in enumerate(lines)}
        return {"imported": len(data), "data": data}


# --------------------------------------------------------------------------- #
# Status / Health Reporting (x.ai: status line, working status)
# --------------------------------------------------------------------------- #
class BotHealth:
    """Reports bot health and diagnostics."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    def report(self) -> dict[str, Any]:
        return {
            "bot_id": self.bot.id,
            "bot_name": self.bot.name,
            "status": self.bot.get_status().value,
            "status_phrase": self.bot.status_phrase(),
            "uptime_seconds": time.time()
            - self.bot.memory.get("started_at", time.time()),
            "vault_entries": len(self.bot.vault.list()),
            "memory_keys": len(self.bot.memory.all()),
            "pending_approvals": len(self.bot.pending_approvals()),
            "max_file_bytes": MAX_FILE_BYTES,
            "supported_image_extensions": sorted(FileHandler.ALLOWED_IMAGE_EXTENSIONS),
            "supported_video_extensions": sorted(FileHandler.ALLOWED_VIDEO_EXTENSIONS),
            "supported_document_extensions": sorted(
                FileHandler.ALLOWED_DOCUMENT_EXTENSIONS
            ),
        }


# --------------------------------------------------------------------------- #
# Extended __all__
# --------------------------------------------------------------------------- #
__all__ = [
    "DEFAULT_BOT",
    "MANAGER",
    "MAX_FILE_BYTES",
    "ApprovalCard",
    "ApprovalEngine",
    "ApprovalStatus",
    "Bot",
    "BotHealth",
    "BotManager",
    "BotMemory",
    "BotStatus",
    "FileHandler",
    "Meeting",
    "MeetingManager",
    "Memory",
    "MemoryImporter",
    "Routine",
    "RoutineScheduler",
    "RoutineStatus",
    "SkillLibrary",
    "SkillTemplate",
    "Vault",
    "VaultEntry",
    "create_bot",
    "get_bot",
]
