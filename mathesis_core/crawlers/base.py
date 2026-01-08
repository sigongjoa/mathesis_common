
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
import logging
from ..exceptions import CrawlerException, CrawlerTimeoutError

logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    """
    Abstract base class for all crawlers
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        headers: Optional[Dict[str, str]] = None
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    @abstractmethod
    async def fetch(self, resource_id: str) -> Dict[str, Any]:
        """Fetch resource by ID"""
        pass

    async def _get(
        self,
        url: str,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> httpx.Response:
        """Helper method for GET requests with retry logic"""
        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response
            except httpx.TimeoutException:
                if retry_count < self.max_retries:
                    logger.warning(f"Timeout crawling {url}, retrying ({retry_count + 1}/{self.max_retries})")
                    return await self._get(url, params, retry_count + 1)
                raise CrawlerTimeoutError(f"Timeout crawling {url} after {self.max_retries} retries")
            except httpx.HTTPError as e:
                raise CrawlerException(f"HTTP Error crawling {url}: {str(e)}")
            except Exception as e:
                raise CrawlerException(f"Unexpected error crawling {url}: {str(e)}")
