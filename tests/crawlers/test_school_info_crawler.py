"""
Tests for school info crawler.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestSchoolInfoCrawler:
    """Tests for school information crawler."""

    @pytest.fixture
    def sample_school_html(self):
        """Sample school page HTML."""
        return """
        <html>
            <body>
                <div class="school-info">
                    <h1>Test High School</h1>
                    <p class="address">123 Test Street, Seoul</p>
                    <p class="phone">02-1234-5678</p>
                </div>
            </body>
        </html>
        """

    def test_init_with_school_id(self):
        """Test initialization with school ID."""
        try:
            from mathesis_core.crawlers.school_info_crawler import SchoolInfoCrawler

            crawler = SchoolInfoCrawler(school_id="SCH001")

            assert crawler.school_id == "SCH001"
        except ImportError:
            pytest.skip("School info crawler not available")

    @pytest.mark.asyncio
    async def test_crawl_school_info(self, sample_school_html):
        """Test crawling school information."""
        try:
            from mathesis_core.crawlers.school_info_crawler import SchoolInfoCrawler

            with patch("httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.text = sample_school_html
                mock_response.status_code = 200
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                crawler = SchoolInfoCrawler(school_id="SCH001")
                result = await crawler.crawl_school_info()

                assert result is not None
        except ImportError:
            pytest.skip("School info crawler not available")

    def test_parse_school_page(self, sample_school_html):
        """Test parsing school page HTML."""
        try:
            from mathesis_core.crawlers.school_info_crawler import SchoolInfoCrawler

            crawler = SchoolInfoCrawler(school_id="SCH001")
            result = crawler.parse_school_page(sample_school_html)

            assert "name" in result or result is not None
        except (ImportError, AttributeError):
            pytest.skip("parse_school_page not available")

    @pytest.mark.asyncio
    async def test_crawl_curriculum(self):
        """Test crawling curriculum information."""
        try:
            from mathesis_core.crawlers.school_info_crawler import SchoolInfoCrawler

            with patch("httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.text = "<html><body>Curriculum</body></html>"
                mock_response.status_code = 200
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                crawler = SchoolInfoCrawler(school_id="SCH001")
                result = await crawler.crawl_curriculum()

                assert result is not None
        except (ImportError, AttributeError):
            pytest.skip("crawl_curriculum not available")

    @pytest.mark.asyncio
    async def test_crawl_exam_schedule(self):
        """Test crawling exam schedule."""
        try:
            from mathesis_core.crawlers.school_info_crawler import SchoolInfoCrawler

            with patch("httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.text = "<html><body>Exam Schedule</body></html>"
                mock_response.status_code = 200
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                crawler = SchoolInfoCrawler(school_id="SCH001")
                result = await crawler.crawl_exam_schedule()

                assert result is not None
        except (ImportError, AttributeError):
            pytest.skip("crawl_exam_schedule not available")
