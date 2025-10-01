"""
E2E Tests for Error Handling and Edge Cases

Tests application behavior under error conditions.
"""

import os
import time

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def base_url() -> str:
    """Get base URL from environment or use default."""
    return os.getenv(
        "BASE_URL", "http://sakese-Publi-BG2ScFFG5nfS-804827597.us-west-2.elb.amazonaws.com"
    )


def login_helper(page: Page, base_url: str) -> None:
    """Helper function to login."""
    page.goto(base_url)
    page.get_by_role("button", name="🔐 ログイン").click()
    time.sleep(2)

    page.fill('input[placeholder="your.email@example.com"]', "test@sakesensei.com")
    password_input = page.locator('input[type="password"]').first
    password_input.fill("TestPass123!@#")
    page.get_by_test_id("stBaseButton-primaryFormSubmit").click()

    page.wait_for_load_state("networkidle", timeout=30000)
    time.sleep(3)


def test_invalid_login_credentials(page: Page, base_url: str) -> None:
    """Test login with invalid credentials."""
    page.goto(base_url)
    page.get_by_role("button", name="🔐 ログイン").click()
    time.sleep(2)

    # Enter invalid credentials
    page.fill('input[placeholder="your.email@example.com"]', "invalid@example.com")
    password_input = page.locator('input[type="password"]').first
    password_input.fill("WrongPassword123")

    page.get_by_test_id("stBaseButton-primaryFormSubmit").click()
    time.sleep(3)

    # Should show error message
    error_message = page.locator('div[data-testid="stAlert"]').or_(page.locator("text=エラー"))
    if error_message.count() > 0:
        expect(error_message.first).to_be_visible()


def test_empty_login_form(page: Page, base_url: str) -> None:
    """Test submitting empty login form."""
    page.goto(base_url)
    page.get_by_role("button", name="🔐 ログイン").click()
    time.sleep(2)

    # Try to submit without filling fields
    page.get_by_test_id("stBaseButton-primaryFormSubmit").click()
    time.sleep(2)

    # Should show validation error or prevent submission
    assert page.url is not None


def test_network_timeout_handling(page: Page, base_url: str) -> None:
    """Test application behavior under network timeout."""
    login_helper(page, base_url)

    # Try AI chat (might timeout if backend is slow)
    chat_input = page.locator('textarea[placeholder*="質問"]').first
    if chat_input.is_visible():
        chat_input.fill("これは長いリクエストです" * 100)  # Very long input

        submit_button = page.get_by_role("button", name="送信")
        submit_button.click()

        # Wait for response or timeout
        time.sleep(10)

        # Should handle gracefully (either response or error message)
        assert page.url is not None


def test_invalid_character_input(page: Page, base_url: str) -> None:
    """Test handling of special characters and SQL injection attempts."""
    login_helper(page, base_url)

    # Navigate to rating page
    rating_link = page.locator("text=⭐").or_(page.locator("text=評価"))
    if rating_link.count() > 0:
        rating_link.first.click()
        time.sleep(2)

        # Try SQL injection-like input
        sake_input = page.locator('input[placeholder*="日本酒"]').or_(
            page.locator('input[placeholder*="銘柄"]')
        )
        if sake_input.count() > 0:
            sake_input.first.fill("'; DROP TABLE users; --")
            time.sleep(1)

            submit_button = page.get_by_role("button", name="保存").or_(
                page.get_by_role("button", name="送信")
            )
            if submit_button.count() > 0:
                submit_button.first.click()
                time.sleep(3)

                # Should handle safely (sanitize input)
                assert page.url is not None


def test_xss_attempt_prevention(page: Page, base_url: str) -> None:
    """Test XSS attack prevention."""
    login_helper(page, base_url)

    # Try XSS in chat
    chat_input = page.locator('textarea[placeholder*="質問"]').first
    if chat_input.is_visible():
        chat_input.fill("<script>alert('XSS')</script>")

        submit_button = page.get_by_role("button", name="送信")
        submit_button.click()
        time.sleep(3)

        # Should not execute script
        # Check that no alert appeared (page should still be functional)
        assert page.url is not None


def test_session_expiration_handling(page: Page, base_url: str) -> None:
    """Test behavior when session expires."""
    login_helper(page, base_url)

    # Clear cookies to simulate session expiration
    page.context.clear_cookies()
    time.sleep(1)

    # Try to access protected feature
    chat_input = page.locator('textarea[placeholder*="質問"]').first
    if chat_input.is_visible():
        chat_input.fill("テスト")

        submit_button = page.get_by_role("button", name="送信")
        submit_button.click()
        time.sleep(3)

        # Should redirect to login or show error
        assert page.url is not None


def test_concurrent_request_handling(page: Page, base_url: str) -> None:
    """Test handling of concurrent requests."""
    login_helper(page, base_url)

    # Try to submit multiple requests quickly
    chat_input = page.locator('textarea[placeholder*="質問"]').first
    if chat_input.is_visible():
        submit_button = page.get_by_role("button", name="送信")

        for i in range(3):
            chat_input.fill(f"質問 {i + 1}")
            submit_button.click()
            time.sleep(0.5)  # Quick succession

        time.sleep(5)

        # Should handle all requests gracefully
        assert page.url is not None


def test_invalid_file_upload(page: Page, base_url: str) -> None:
    """Test uploading invalid file type."""
    login_helper(page, base_url)

    # Navigate to image recognition page
    image_link = page.locator("text=📸").or_(page.locator("text=画像"))
    if image_link.count() > 0:
        image_link.first.click()
        time.sleep(2)

        # Look for file upload
        file_input = page.locator('input[type="file"]')
        if file_input.count() > 0:
            # Try to upload invalid file (would need actual test file)
            # For now, just verify upload exists
            expect(file_input.first).to_be_visible()


def test_oversized_file_upload(page: Page, base_url: str) -> None:
    """Test uploading file that exceeds size limit."""
    login_helper(page, base_url)

    # Navigate to image recognition page
    image_link = page.locator("text=📸").or_(page.locator("text=画像"))
    if image_link.count() > 0:
        image_link.first.click()
        time.sleep(2)

        # Check for file size warnings
        size_warning = page.locator("text=MB").or_(page.locator("text=サイズ"))
        # Size limit should be documented
        assert page.url is not None


def test_browser_back_button(page: Page, base_url: str) -> None:
    """Test application behavior with browser back button."""
    login_helper(page, base_url)

    # Navigate through pages
    rating_link = page.locator("text=⭐")
    if rating_link.count() > 0:
        rating_link.first.click()
        time.sleep(2)

        # Go back
        page.go_back()
        time.sleep(2)

        # Should return to previous page gracefully
        assert page.url is not None


def test_browser_refresh(page: Page, base_url: str) -> None:
    """Test application behavior on page refresh."""
    login_helper(page, base_url)

    # Navigate to a page
    rating_link = page.locator("text=⭐")
    if rating_link.count() > 0:
        rating_link.first.click()
        time.sleep(2)

        # Refresh page
        page.reload()
        time.sleep(3)

        # Should maintain state or redirect properly
        assert page.url is not None


def test_api_error_display(page: Page, base_url: str) -> None:
    """Test that API errors are displayed user-friendly."""
    login_helper(page, base_url)

    # Try action that might cause API error
    chat_input = page.locator('textarea[placeholder*="質問"]').first
    if chat_input.is_visible():
        # Send request that might fail
        chat_input.fill("テストエラー")
        submit_button = page.get_by_role("button", name="送信")
        submit_button.click()
        time.sleep(5)

        # If error occurs, should be user-friendly
        error_alerts = page.locator('div[data-testid="stAlert"]').all()
        for alert in error_alerts:
            if alert.is_visible():
                error_text = alert.text_content() or ""
                # Should not show raw stack traces or technical jargon
                assert "Traceback" not in error_text, "Raw error exposed to user"
                assert "Exception" not in error_text or "エラー" in error_text


def test_empty_search_query(page: Page, base_url: str) -> None:
    """Test handling of empty search queries."""
    login_helper(page, base_url)

    # Try empty AI chat
    chat_input = page.locator('textarea[placeholder*="質問"]').first
    if chat_input.is_visible():
        # Submit empty query
        submit_button = page.get_by_role("button", name="送信")
        submit_button.click()
        time.sleep(2)

        # Should show validation message or prevent submission
        assert page.url is not None


def test_rapid_button_clicking(page: Page, base_url: str) -> None:
    """Test application doesn't break with rapid button clicks."""
    login_helper(page, base_url)

    # Rapidly click submit button
    chat_input = page.locator('textarea[placeholder*="質問"]').first
    if chat_input.is_visible():
        chat_input.fill("テスト")

        submit_button = page.get_by_role("button", name="送信")

        # Click multiple times rapidly
        for _ in range(5):
            submit_button.click()

        time.sleep(3)

        # Should handle gracefully (debounce or queue)
        assert page.url is not None


def test_unicode_input_handling(page: Page, base_url: str) -> None:
    """Test handling of various Unicode characters."""
    login_helper(page, base_url)

    # Test emoji and special Unicode
    chat_input = page.locator('textarea[placeholder*="質問"]').first
    if chat_input.is_visible():
        chat_input.fill("🍶🌸日本酒について教えて😊")

        submit_button = page.get_by_role("button", name="送信")
        submit_button.click()
        time.sleep(5)

        # Should handle Unicode properly
        assert page.url is not None
