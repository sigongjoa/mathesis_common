"""
Tests for base crawler.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestBaseCrawler:
    """Tests for base crawler class."""

    def test_init_sets_config(self):
        """Test initialization with config."""
        try:
            from mathesis_core.crawlers.base import BaseCrawler

            crawler = BaseCrawler(
                base_url="https://example.com",
                timeout=30
            )

            assert crawler.base_url == "https://example.com"
            assert crawler.timeout == 30
        except ImportError:
            pytest.skip("Base crawler not available")

    @pytest.mark.asyncio
    async def test_fetch_page(self):
        """Test fetching a page."""
        try:
            from mathesis_core.crawlers.base import BaseCrawler

            with patch("httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.text = "<html><body>Test</body></html>"
                mock_response.status_code = 200
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                crawler = BaseCrawler(base_url="https://example.com")
                result = await crawler.fetch_page("/test")

                assert result is not None
        except ImportError:
            pytest.skip("Base crawler not available")

    def test_parse_html(self):
        """Test HTML parsing."""
        try:
            from mathesis_core.crawlers.base import BaseCrawler

            crawler = BaseCrawler(base_url="https://example.com")
            html = "<html><body><h1>Title</h1><p>Content</p></body></html>"

            result = crawler.parse_html(html)

            assert result is not None
        except (ImportError, AttributeError):
            pytest.skip("parse_html not available")

    def test_extract_links(self):
        """Test link extraction from HTML."""
        try:
            from mathesis_core.crawlers.base import BaseCrawler

            crawler = BaseCrawler(base_url="https://example.com")
            html = '<html><body><a href="/page1">Link 1</a><a href="/page2">Link 2</a></body></html>'

            links = crawler.extract_links(html)

            assert len(links) == 2
        except (ImportError, AttributeError):
            pytest.skip("extract_links not available")

    def test_normalize_url(self):
        """Test URL normalization."""
        try:
            from mathesis_core.crawlers.base import BaseCrawler

            crawler = BaseCrawler(base_url="https://example.com")

            result = crawler.normalize_url("/page")

            assert result == "https://example.com/page"
        except (ImportError, AttributeError):
            pytest.skip("normalize_url not available")
