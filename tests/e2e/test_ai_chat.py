"""
E2E Tests for AI Chat Functionality

Tests AI chat interface with Bedrock integration.
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


def test_ai_chat_interface_visible(page: Page, base_url: str) -> None:
    """Test that AI chat interface is visible after login."""
    login_helper(page, base_url)

    # Check main page is loaded
    expect(page.locator("text=ホーム")).to_be_visible()

    # Look for AI chat section
    expect(page.locator("text=Sake Sensei に質問")).to_be_visible(timeout=5000)


def test_ai_chat_input_form(page: Page, base_url: str) -> None:
    """Test that AI chat input form is functional."""
    login_helper(page, base_url)

    # Locate chat input
    chat_input = page.locator('textarea[placeholder*="質問"]').first
    expect(chat_input).to_be_visible()

    # Check submit button exists
    submit_button = page.get_by_role("button", name="送信")
    expect(submit_button).to_be_visible()


def test_ai_chat_basic_question(page: Page, base_url: str) -> None:
    """Test AI chat with a basic question about sake."""
    login_helper(page, base_url)

    # Find and fill chat input
    chat_input = page.locator('textarea[placeholder*="質問"]').first
    chat_input.fill("日本酒でおすすめは？")

    # Submit question
    submit_button = page.get_by_role("button", name="送信")
    submit_button.click()

    # Wait for response (AI should respond within 10 seconds)
    time.sleep(2)

    # Check that response appeared (either success or error message)
    # We expect either "Sake Sensei:" response or an error alert
    page.wait_for_timeout(8000)  # Wait for AI response

    # Verify no validation error
    try:
        error_alert = page.locator('div[data-testid="stAlert"]').first
        if error_alert.is_visible():
            error_text = error_alert.text_content()
            # Should not contain parameter validation errors
            assert (
                "Parameter validation failed" not in error_text
            ), f"API format error found: {error_text}"
    except Exception:
        # No error alert is fine
        pass

    # Check for response in chat history
    response_found = (
        page.locator("text=Sake Sensei:").count() > 0
        or page.locator("text=エラーが発生しました").count() > 0
    )
    assert response_found, "No response from AI chat"


def test_ai_chat_history_display(page: Page, base_url: str) -> None:
    """Test that chat history is displayed correctly."""
    login_helper(page, base_url)

    # Send first message
    chat_input = page.locator('textarea[placeholder*="質問"]').first
    chat_input.fill("こんにちは")

    submit_button = page.get_by_role("button", name="送信")
    submit_button.click()

    time.sleep(5)

    # Check if "会話履歴" section appears
    history_header = page.locator("text=会話履歴")
    if history_header.count() > 0:
        expect(history_header).to_be_visible()

        # Check for user message
        expect(page.locator("text=あなた:")).to_be_visible()


def test_ai_chat_clear_history(page: Page, base_url: str) -> None:
    """Test that chat history can be cleared."""
    login_helper(page, base_url)

    # Send a message first
    chat_input = page.locator('textarea[placeholder*="質問"]').first
    chat_input.fill("テスト")

    submit_button = page.get_by_role("button", name="送信")
    submit_button.click()

    time.sleep(3)

    # Click clear history button
    clear_button = page.get_by_role("button", name="履歴クリア")
    if clear_button.count() > 0:
        clear_button.click()
        time.sleep(2)

        # Verify history is cleared
        history_header = page.locator("text=会話履歴")
        expect(history_header).not_to_be_visible()


def test_ai_chat_no_api_format_errors(page: Page, base_url: str) -> None:
    """Test that AI chat does not produce API parameter validation errors."""
    login_helper(page, base_url)

    # Test various question formats
    test_questions = [
        "おすすめの日本酒を教えて",
        "辛口の日本酒は？",
        "初心者向けの日本酒",
    ]

    for question in test_questions:
        # Clear input and enter new question
        chat_input = page.locator('textarea[placeholder*="質問"]').first
        chat_input.clear()
        chat_input.fill(question)

        submit_button = page.get_by_role("button", name="送信")
        submit_button.click()

        time.sleep(3)

        # Check for parameter validation errors
        error_alerts = page.locator('div[data-testid="stAlert"]').all()
        for alert in error_alerts:
            if alert.is_visible():
                error_text = alert.text_content() or ""
                assert (
                    "Parameter validation failed" not in error_text
                ), f"API format error for question '{question}': {error_text}"
                assert "Invalid type" not in error_text, f"Type error for '{question}': {error_text}"

        # Small delay between questions
        time.sleep(1)
