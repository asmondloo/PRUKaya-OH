import threading
from bot.utils.logger_utils import setup_logger
import time
from typing import Set


logger = setup_logger()

class BotStatusManager:
    def __init__(self, bot):
        self.bot = bot
        self.active_users: Set[int] = set()
        self.running = True
        self.status_thread = threading.Thread(target=self._status_loop, daemon=True)
        
    def start(self):
        self.running = True
        self.status_thread.start()
        
    def stop(self):
        self.running = False
        if self.status_thread.is_alive():
            self.status_thread.join()
            
    def add_user(self, user_id: int):
        self.active_users.add(user_id)
        
    def remove_user(self, user_id: int):
        if user_id in self.active_users:
            self.active_users.remove(user_id)
            
    def _status_loop(self):
        while self.running:
            for user_id in list(self.active_users):
                try:
                    self.bot.send_chat_action(user_id, 'typing')
                except Exception as e:
                    logger.error(f"Error sending online status to user {user_id}: {str(e)}")
            time.sleep(4)
