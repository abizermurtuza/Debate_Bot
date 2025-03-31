import os
import threading
import logging
from typing import List, Dict
import atexit

class TempFileManager:
    def __init__(self):
        self._temp_files: List[str] = []
        self._locks: Dict[str, threading.Lock] = {}
        self._lock = threading.Lock()
        atexit.register(self.cleanup_all)

    def register_file(self, filepath: str) -> None:
        """Register a temporary file for tracking."""
        with self._lock:
            self._temp_files.append(filepath)
            self._locks[filepath] = threading.Lock()

    def get_lock(self, filepath: str) -> threading.Lock:
        """Get the lock for a specific file."""
        return self._locks.get(filepath, threading.Lock())

    def remove_file(self, filepath: str) -> None:
        """Safely remove a temporary file."""
        if not filepath or not os.path.exists(filepath):
            return

        lock = self.get_lock(filepath)
        with lock:
            try:
                os.remove(filepath)
                with self._lock:
                    if filepath in self._temp_files:
                        self._temp_files.remove(filepath)
                    if filepath in self._locks:
                        del self._locks[filepath]
            except Exception as e:
                logging.warning(f"Failed to remove temporary file {filepath}: {e}")

    def cleanup_all(self) -> None:
        """Clean up all registered temporary files."""
        with self._lock:
            files_to_clean = self._temp_files.copy()
            
        for filepath in files_to_clean:
            self.remove_file(filepath)

temp_file_manager = TempFileManager()
