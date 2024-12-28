import threading
import time
from typing import Dict, List
import uuid
from datetime import timedelta, datetime
from dataclasses import dataclass, field
from bot.utils.logger_utils import setup_logger

logger = setup_logger()

@dataclass
class ChatMessage:
    role: str
    content: str

@dataclass
class UserSession:
    session_id: str
    last_active: datetime
    processing: bool = False
    chat_history: List[ChatMessage] = field(default_factory=list)

class SessionManager:
    def __init__(self, timeout_minutes: int = 5):
        self.sessions: Dict[int, UserSession] = {}
        self.timeout = timedelta(minutes=timeout_minutes)
        self.lock = threading.Lock()
        
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def _cleanup_loop(self):
        while True:
            self.clear_expired_sessions()
            time.sleep(60)  
    
    def clear_expired_sessions(self):
        now = datetime.now()
        with self.lock:
            expired_users = [
                user_id for user_id, session in self.sessions.items()
                if (now - session.last_active) > self.timeout
            ]
            
            for user_id in expired_users:
                session_id = self.sessions[user_id].session_id
                logger.info(f"[CLEAR] Session {session_id}: Cleared due to inactivity after {self.timeout.total_seconds()/60} minutes.")
                del self.sessions[user_id]
    
    def get_or_create_session(self, user_id: int, username: str) -> UserSession:
        now = datetime.now()
        with self.lock:
            if user_id not in self.sessions:
                session_id = str(uuid.uuid4())
                self.sessions[user_id] = UserSession(
                    session_id=session_id,
                    last_active=now
                )
                logger.info(f"[CREATE] Session {session_id}: Created for {username}.")
            else:
                current_session = self.sessions[user_id]
                # Check if session should be refreshed
                if (now - current_session.last_active) > timedelta(minutes=2):  # Refresh after 2 minutes of inactivity
                    session_id = str(uuid.uuid4())
                    logger.info(f"[NEW] Session {session_id}: Created new session for {username} (old session expired).")
                    self.sessions[user_id] = UserSession(
                        session_id=session_id,
                        last_active=now
                    )
                else:
                    current_session.last_active = now
                    logger.info(f"[REFRESH] Session {current_session.session_id}: Refreshed for {username} at {now}.")
            
            return self.sessions[user_id]

    def get_chat_history(self, user_id: int) -> List[ChatMessage]:
        if user_id in self.sessions:
            return self.sessions[user_id].chat_history
        return []

    def add_to_chat_history(self, user_id: int, role: str, content: str):
        if user_id in self.sessions:
            self.sessions[user_id].chat_history.append(ChatMessage(role=role, content=content))
