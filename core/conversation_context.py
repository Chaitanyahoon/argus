"""
Conversation context management — maintain user conversation history for improved Gemini context.
Provides multi-turn conversation tracking with TTL for memory efficiency.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)

# ── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class ConversationMessage:
    """Represents a single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API calls."""
        return {
            "role": self.role,
            "content": self.content,
        }


@dataclass
class UserConversation:
    """Tracks a user's conversation history."""
    user_id: int
    guild_id: int
    messages: List[ConversationMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append(ConversationMessage(role=role, content=content))
        self.last_active = datetime.now()
    
    def is_expired(self, ttl_minutes: int = 60) -> bool:
        """Check if conversation has expired."""
        return datetime.now() - self.last_active > timedelta(minutes=ttl_minutes)
    
    def get_context(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get last N messages as API context."""
        # Return most recent messages, excluding the current incomplete turn
        messages = self.messages[-max_messages:]
        return [msg.to_dict() for msg in messages]
    
    def clear_context(self) -> None:
        """Clear all messages (start fresh conversation)."""
        self.messages.clear()
        self.last_active = datetime.now()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get conversation summary."""
        return {
            'user_id': self.user_id,
            'guild_id': self.guild_id,
            'message_count': len(self.messages),
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat(),
            'duration_minutes': round((datetime.now() - self.created_at).total_seconds() / 60, 1),
        }


# ── Context Manager ──────────────────────────────────────────────────────────

class ConversationContextManager:
    """Manages conversation history across all users and guilds with persistence."""
    
    def __init__(self, ttl_minutes: int = 60, max_conversations: int = 1000, persist_dir: str = "data/conversations"):
        """
        Args:
            ttl_minutes: Time-to-live for inactive conversations
            max_conversations: Maximum conversations to keep in memory
            persist_dir: Directory to persist conversations to JSON
        """
        import os
        from pathlib import Path
        
        self.ttl_minutes = ttl_minutes
        self.max_conversations = max_conversations
        self.conversations: Dict[tuple, UserConversation] = {}  # {(user_id, guild_id): conversation}
        self._cleanup_task = None
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Load persisted conversations on init
        self._load_persisted_conversations()
        logger.info(f"Conversation manager initialized (TTL: {ttl_minutes}m, persist_dir: {persist_dir})")
    
    def _get_key(self, user_id: int, guild_id: int) -> tuple:
        """Get conversation key."""
        return (user_id, guild_id)
    
    def _get_persist_file(self, user_id: int, guild_id: int) -> Path:
        """Get file path for persisting conversation."""
        return self.persist_dir / f"conv_{user_id}_{guild_id}.json"
    
    def _load_persisted_conversations(self) -> None:
        """Load all persisted conversations from disk."""
        import json
        
        try:
            for file in self.persist_dir.glob("conv_*.json"):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    user_id = data.get('user_id')
                    guild_id = data.get('guild_id')
                    if not user_id or not guild_id:
                        continue
                    
                    key = self._get_key(user_id, guild_id)
                    conv = UserConversation(user_id=user_id, guild_id=guild_id)
                    
                    # Restore messages
                    for msg_data in data.get('messages', []):
                        conv.messages.append(
                            ConversationMessage(
                                role=msg_data['role'],
                                content=msg_data['content'],
                                timestamp=datetime.fromisoformat(msg_data['timestamp'])
                            )
                        )
                    
                    self.conversations[key] = conv
                    logger.debug(f"Loaded conversation: user {user_id}, guild {guild_id} ({len(conv.messages)} messages)")
                except Exception as e:
                    logger.error(f"Error loading conversation from {file}: {e}")
        except Exception as e:
            logger.error(f"Error loading persisted conversations: {e}")
    
    def _save_conversation(self, user_id: int, guild_id: int) -> None:
        """Persist conversation to disk."""
        import json
        
        key = self._get_key(user_id, guild_id)
        if key not in self.conversations:
            return
        
        conv = self.conversations[key]
        file_path = self._get_persist_file(user_id, guild_id)
        
        try:
            data = {
                'user_id': conv.user_id,
                'guild_id': conv.guild_id,
                'created_at': conv.created_at.isoformat(),
                'last_active': conv.last_active.isoformat(),
                'messages': [
                    {
                        'role': msg.role,
                        'content': msg.content,
                        'timestamp': msg.timestamp.isoformat()
                    }
                    for msg in conv.messages
                ]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved conversation: user {user_id}, guild {guild_id}")
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    def get_or_create(self, user_id: int, guild_id: int) -> UserConversation:
        """Get existing conversation or create new one."""
        key = self._get_key(user_id, guild_id)
        
        if key not in self.conversations:
            self.conversations[key] = UserConversation(
                user_id=user_id,
                guild_id=guild_id
            )
            logger.debug(f"Created new conversation: user {user_id}, guild {guild_id}")
        
        return self.conversations[key]
    
    def add_message(self, user_id: int, guild_id: int, role: str, content: str) -> None:
        """Add message to conversation and persist."""
        conv = self.get_or_create(user_id, guild_id)
        conv.add_message(role, content)
        self._save_conversation(user_id, guild_id)  # Auto-save on message
        logger.debug(f"Added message to {user_id}@{guild_id}: {role} ({len(content)} chars)")
    
    def add_user_message(self, user_id: int, guild_id: int, content: str) -> None:
        """Add user message to conversation."""
        conv = self.get_or_create(user_id, guild_id)
        conv.add_message("user", content)
    
    def add_assistant_message(self, user_id: int, guild_id: int, content: str) -> None:
        """Add assistant (Gemini) response to conversation."""
        conv = self.get_or_create(user_id, guild_id)
        conv.add_message("assistant", content)
    
    def get_context(self, user_id: int, guild_id: int, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get conversation context for API calls."""
        key = self._get_key(user_id, guild_id)
        
        if key not in self.conversations:
            return []
        
        return self.conversations[key].get_context(max_messages)
    
    def clear_conversation(self, user_id: int, guild_id: int) -> None:
        """Clear conversation history for user."""
        key = self._get_key(user_id, guild_id)
        
        if key in self.conversations:
            self.conversations[key].clear_context()
            logger.info(f"Cleared conversation for user {user_id}")
    
    def delete_conversation(self, user_id: int, guild_id: int) -> None:
        """Delete conversation entirely."""
        key = self._get_key(user_id, guild_id)
        
        if key in self.conversations:
            del self.conversations[key]
            logger.info(f"Deleted conversation for user {user_id}")
    
    def cleanup_expired(self) -> int:
        """Remove expired conversations. Returns number removed."""
        expired_keys = [
            key for key, conv in self.conversations.items()
            if conv.is_expired(self.ttl_minutes)
        ]
        
        for key in expired_keys:
            del self.conversations[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired conversations")
        
        return len(expired_keys)
    
    def cleanup_memory_size(self) -> int:
        """Remove oldest conversations if exceeding max size. Returns number removed."""
        if len(self.conversations) <= self.max_conversations:
            return 0
        
        # Remove oldest conversations
        sorted_convs = sorted(
            self.conversations.items(),
            key=lambda x: x[1].last_active
        )
        
        to_remove = len(self.conversations) - self.max_conversations
        removed_keys = [key for key, _ in sorted_convs[:to_remove]]
        
        for key in removed_keys:
            del self.conversations[key]
        
        logger.warning(f"Memory cleanup: removed {to_remove} conversations (limit: {self.max_conversations})")
        return to_remove
    
    async def start_cleanup_loop(self, interval_minutes: int = 15) -> None:
        """Start background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(interval_minutes * 60)
                expired = self.cleanup_expired()
                oversized = self.cleanup_memory_size()
                
                stats = self.get_stats()
                logger.debug(
                    f"Cleanup: expired={expired}, oversized={oversized}, "
                    f"active={stats['active_conversations']}"
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context manager statistics."""
        total_messages = sum(len(c.messages) for c in self.conversations.values())
        
        return {
            'active_conversations': len(self.conversations),
            'total_messages': total_messages,
            'avg_messages_per_conv': round(total_messages / len(self.conversations), 1) if self.conversations else 0,
            'max_ttl_minutes': self.ttl_minutes,
            'max_conversations': self.max_conversations,
        }
    
    def get_user_summary(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get summary of user's conversations."""
        user_convs = [
            conv for key, conv in self.conversations.items()
            if key[0] == user_id
        ]
        
        if not user_convs:
            return None
        
        total_messages = sum(len(c.messages) for c in user_convs)
        
        return {
            'user_id': user_id,
            'guilds_active': len(user_convs),
            'total_messages': total_messages,
            'conversations': [c.get_summary() for c in user_convs],
        }


# Global instance
_global_context_manager: Optional[ConversationContextManager] = None

def initialize_context_manager(ttl_minutes: int = 60, max_conversations: int = 1000) -> ConversationContextManager:
    """Initialize global context manager."""
    global _global_context_manager
    _global_context_manager = ConversationContextManager(ttl_minutes, max_conversations)
    logger.info(f"Conversation context manager initialized (TTL: {ttl_minutes}m, Max: {max_conversations})")
    return _global_context_manager

def get_context_manager() -> Optional[ConversationContextManager]:
    """Get global context manager."""
    return _global_context_manager

def get_conversation_context(user_id: int, guild_id: int, max_messages: int = 10) -> List[Dict[str, str]]:
    """Get conversation context (helper function)."""
    if not _global_context_manager:
        return []
    return _global_context_manager.get_context(user_id, guild_id, max_messages)

def add_to_context(user_id: int, guild_id: int, role: str, content: str) -> None:
    """Add message to context (helper function)."""
    if _global_context_manager:
        if role == "user":
            _global_context_manager.add_user_message(user_id, guild_id, content)
        else:
            _global_context_manager.add_assistant_message(user_id, guild_id, content)
