import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from src.updater import AutoUpdater, CheckStatus, UpdateInfo


class TestUpdaterHttp304(unittest.TestCase):
    """Test suite ensuring AutoUpdater properly handles HTTP 304 and force refresh."""

    def setUp(self):
        self.updater = AutoUpdater(current_version="1.0.4")

    @patch("urllib.request.urlopen")
    def test_check_for_updates_handles_http_304_with_cached_info(self, mock_urlopen):
        """When GitHub returns HTTP 304 Not Modified, cached info should be returned as UP_TO_DATE."""
        # Setup pre-cached info
        cached_info = UpdateInfo(
            version="1.0.4",
            tag_name="v1.0.4",
            release_name="Speech-To-Text v1.0.4",
            release_notes="Fixes",
            published_at="2026-10-17T18:00:00Z",
            is_update_available=False,
            status=CheckStatus.UP_TO_DATE,
        )
        self.updater._cached_etag = 'W/"test-etag-123"'
        self.updater._cached_info = cached_info

        # Simulate urllib raising HTTP 304
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.github.com/...",
            code=304,
            msg="Not Modified",
            hdrs={},
            fp=None,
        )

        result = self.updater.check_for_updates(timeout=5, force=False)

        self.assertIsNotNone(result)
        self.assertNotEqual(result.status, CheckStatus.ERROR, "HTTP 304 must NOT be treated as an error")
        self.assertEqual(result.status, CheckStatus.UP_TO_DATE)
        self.assertFalse(result.is_update_available)
        self.assertIsNone(result.error_message)

    @patch("urllib.request.urlopen")
    def test_check_for_updates_handles_http_304_when_update_available_cached(self, mock_urlopen):
        """When HTTP 304 occurs and cached info had a newer version, UPDATE_AVAILABLE is maintained."""
        cached_info = UpdateInfo(
            version="1.0.5",
            tag_name="v1.0.5",
            release_name="Speech-To-Text v1.0.5",
            release_notes="New features",
            published_at="2026-10-17T18:00:00Z",
            is_update_available=True,
            status=CheckStatus.UPDATE_AVAILABLE,
        )
        self.updater._cached_etag = 'W/"test-etag-123"'
        self.updater._cached_info = cached_info

        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.github.com/...",
            code=304,
            msg="Not Modified",
            hdrs={},
            fp=None,
        )

        result = self.updater.check_for_updates(timeout=5, force=False)

        self.assertIsNotNone(result)
        self.assertEqual(result.status, CheckStatus.UPDATE_AVAILABLE)
        self.assertTrue(result.is_update_available)
        self.assertEqual(result.version, "1.0.5")

    @patch("urllib.request.urlopen")
    def test_check_for_updates_force_bypasses_if_none_match(self, mock_urlopen):
        """When force=True is passed, If-None-Match header must NOT be sent."""
        self.updater._cached_etag = 'W/"test-etag-123"'

        # Return mock 200 response with payload
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers.get.return_value = 'W/"new-etag-456"'
        mock_response.read.return_value = b'{"tag_name": "v1.0.4", "name": "v1.0.4", "body": "", "published_at": "", "assets": []}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        self.updater.check_for_updates(timeout=5, force=True)

        call_args = mock_urlopen.call_args[0][0]
        self.assertNotIn("If-none-match", [h.lower() for h in call_args.headers.keys()])


if __name__ == "__main__":
    unittest.main()
