import json
import os
from datetime import datetime

class PromptLogger:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        
    def log_interaction(self, origin: str, content: dict | str):
        """Log an interaction with timestamp by appending to the file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = {
            "timestamp": timestamp,
            "origin": origin,
            "content": content
        }
        
        # Convert to pretty JSON string
        log_str = json.dumps(log_entry, indent=2)
        
        # Append to file
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            f.write(log_str + "\n")  # Add newline between entries