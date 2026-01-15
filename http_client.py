"""Async HTTP client with connection pooling and retry logic."""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging


class RetryStrategy(Enum):
    """Retry strategy options."""
    EXPONENTIAL_BACKOFF = "exponential"
    LINEAR_BACKOFF = "linear"
    FIXED_DELAY = "fixed"


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    backoff_factor: float = 2.0


class AsyncHttpClient:
    """Async HTTP client with connection pooling and retry logic."""
    
    def __init__(self, timeout: int = 30, max_connections: int = 100):
        self.timeout_seconds = timeout
        self.max_connections = max_connections
        self.timeout = None
        self.connector = None
        self._session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def start(self):
        """Start the HTTP session."""
        if self._session is None or self._session.closed:
            # Initialize timeout and connector inside async context
            if self.timeout is None:
                self.timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            
            if self.connector is None:
                self.connector = aiohttp.TCPConnector(
                    limit=self.max_connections,
                    limit_per_host=10,
                    keepalive_timeout=30,
                    enable_cleanup_closed=True
                )
            
            self._session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=self.timeout
            )
    
    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
        if self.connector and not self.connector.closed:
            await self.connector.close()
    
    @property
    def session(self) -> aiohttp.ClientSession:
        """Get the current session."""
        if self._session is None or self._session.closed:
            raise RuntimeError("HTTP session not started. Use async with or call start().")
        return self._session
    
    def _calculate_delay(self, attempt: int, retry_config: RetryConfig) -> float:
        """Calculate delay for retry attempt."""
        if retry_config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = retry_config.base_delay * (retry_config.backoff_factor ** (attempt - 1))
        elif retry_config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = retry_config.base_delay * attempt
        else:  # FIXED_DELAY
            delay = retry_config.base_delay
        
        return min(delay, retry_config.max_delay)
    
    async def request_with_retry(
        self,
        method: str,
        url: str,
        retry_config: Optional[RetryConfig] = None,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """Make HTTP request with retry logic."""
        if retry_config is None:
            retry_config = RetryConfig()
        
        last_exception = None
        
        for attempt in range(1, retry_config.max_attempts + 1):
            try:
                response = await self.session.request(method, url, **kwargs)
                
                # Check if response is successful or should be retried
                if response.status < 500:  # Don't retry client errors (4xx)
                    return response
                
                # Server error - close response and retry
                response.close()
                
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                self.logger.warning(f"Request failed (attempt {attempt}/{retry_config.max_attempts}): {e}")
            
            # Don't delay after last attempt
            if attempt < retry_config.max_attempts:
                delay = self._calculate_delay(attempt, retry_config)
                await asyncio.sleep(delay)
        
        # All attempts failed
        raise last_exception or aiohttp.ClientError(f"All {retry_config.max_attempts} attempts failed")
    
    async def get_json(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_config: Optional[RetryConfig] = None
    ) -> Dict[str, Any]:
        """Make GET request and return JSON response."""
        async with await self.request_with_retry(
            'GET', url, retry_config=retry_config, headers=headers, params=params
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_text(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_config: Optional[RetryConfig] = None
    ) -> str:
        """Make GET request and return text response."""
        async with await self.request_with_retry(
            'GET', url, retry_config=retry_config, headers=headers, params=params
        ) as response:
            response.raise_for_status()
            return await response.text()


# Global HTTP client instance
http_client = AsyncHttpClient()