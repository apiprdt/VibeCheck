import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from vibecheck import __version__

class VibeCache:
    """Manages caching of LLM responses to improve performance and reduce costs."""

    def __init__(self, cache_dir: Path | None = None):
        if cache_dir is None:
            self.cache_dir = Path.home() / ".vibecheck" / "cache"
        else:
            self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _generate_key(self, **kwargs) -> str:
        """Generate a unique hash key based on input arguments."""
        # Convert all inputs to a stable string representation
        input_data = json.dumps(kwargs, sort_keys=True)
        return hashlib.sha256(input_data.encode()).hexdigest()

    def get(self, **kwargs) -> Optional[Any]:
        """Retrieve a cached response if it exists and is still valid (TTL 7 days)."""
        key = self._generate_key(**kwargs)
        cache_file = self.cache_dir / f"{key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Validasi: Apakah versinya sama? (Mencegah bug bawaan dari versi lama)
                if data.get("vibecheck_version") != __version__:
                    return None
                    
                # Validasi: Apakah sudah lebih dari 7 hari (604800 detik)?
                if time.time() - data.get("timestamp", 0) > 604800:
                    return None
                    
                return data.get("payload")
            except Exception:
                return None
        return None

    def set(self, value: Any, **kwargs) -> None:
        """Store a response in the cache with metadata."""
        key = self._generate_key(**kwargs)
        cache_file = self.cache_dir / f"{key}.json"
        
        data = {
            "vibecheck_version": __version__,
            "timestamp": time.time(),
            "payload": value
        }
        
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

# Global cache instance
cache = VibeCache()
