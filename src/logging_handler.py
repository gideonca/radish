import os
from pathlib import Path
from datetime import datetime

class LoggingHandler:
    def __init__(self, log_file=None):
        # Check for .radish/logs directory in home directory
        home_dir = Path.home()
        log_dir = home_dir / '.radish' / 'logs'
        
        # Create directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate log file name with date: radish_yyyy_mm_dd.log
        date_str = datetime.now().strftime('%Y_%m_%d')
        log_filename = f'radish_{date_str}.log'
        server_log_file = f'server_{date_str}.log'
        
        self.log_file = str(log_dir / log_filename)
        self.server_log_file = str(log_dir / server_log_file)

    def log_message(self, message):
        with open(self.log_file, 'a') as file:
            file.write(message + '\n')
            
    def log_server_message(self, message):
        with open(self.server_log_file, 'a') as file:
            file.write(message + '\n')

    def get_log_messages(self):
        with open(self.log_file, 'r') as file:
            messages = file.readlines()
        return [message.strip() for message in messages]