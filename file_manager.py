"""Async file operations with proper error handling and locking."""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import aiofiles
import aiofiles.os
from contextlib import asynccontextmanager


class FileManager:
    """Async file manager with locking support."""
    
    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}
    
    def _get_lock(self, file_path: str) -> asyncio.Lock:
        """Get or create a lock for a specific file path."""
        if file_path not in self._locks:
            self._locks[file_path] = asyncio.Lock()
        return self._locks[file_path]
    
    @asynccontextmanager
    async def locked_file_operation(self, file_path: str):
        """Context manager for locked file operations."""
        lock = self._get_lock(file_path)
        async with lock:
            yield
    
    async def read_json_file(self, file_path: str, default: Any = None) -> Any:
        """Safely read a JSON file with error handling."""
        path = Path(file_path)
        
        if not await aiofiles.os.path.exists(path):
            if default is not None:
                return default
            raise FileNotFoundError(f"File {file_path} not found")
        
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            raise IOError(f"Error reading {file_path}: {e}")
    
    async def write_json_file(self, file_path: str, data: Any, create_dirs: bool = True) -> None:
        """Safely write data to a JSON file with error handling."""
        path = Path(file_path)
        
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Write to temp file first, then rename (atomic operation)
            temp_path = path.with_suffix('.tmp')
            
            async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2))
            
            # Atomic rename
            await aiofiles.os.rename(temp_path, path)
            
        except Exception as e:
            # Clean up temp file if it exists
            if await aiofiles.os.path.exists(temp_path):
                await aiofiles.os.remove(temp_path)
            raise IOError(f"Error writing {file_path}: {e}")


# Global file manager instance
file_manager = FileManager()