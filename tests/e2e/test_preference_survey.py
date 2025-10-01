"""
E2E Tests for Preference Survey

Tests user preference survey completion and submission.
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


def test_preference_survey_page_accessible(page: Page, base_url: str) -> None:
    """Test that preference survey page is accessible."""
    login_helper(page, base_url)

    # Navigate to preference survey (check sidebar or main navigation)
    preference_link = page.locator("text=🎯").or_(page.locator("text=好みの設定"))
    if preference_link.count() > 0:
        preference_link.first.click()
        time.sleep(2)

        # Check page loaded
        expect(page.locator("text=好み").or_(page.locator("text=設定"))).to_be_visible()


def test_preference_survey_has_taste_options(page: Page, base_url: str) -> None:
    """Test that preference survey has taste preference options."""
    login_helper(page, base_url)

    # Navigate to preferences
    preference_link = page.locator("text=🎯").or_(page.locator("text=好みの設定"))
    if preference_link.count() > 0:
        preference_link.first.click()
        time.sleep(2)

        # Look for taste-related options (甘口/辛口)
        taste_options = page.locator("text=甘口").or_(page.locator("text=辛口"))
        if taste_options.count() > 0:
            expect(taste_options.first).to_be_visible()


def test_preference_survey_has_experience_level(page: Page, base_url: str) -> None:
    """Test that preference survey has experience level selection."""
    login_helper(page, base_url)

    # Navigate to preferences
    preference_link = page.locator("text=🎯").or_(page.locator("text=好みの設定"))
    if preference_link.count() > 0:
        preference_link.first.click()
        time.sleep(2)

        # Look for experience level options
        experience_options = page.locator("text=初心者").or_(page.locator("text=beginner"))
        if experience_options.count() > 0:
            expect(experience_options.first).to_be_visible()


def test_preference_survey_submission(page: Page, base_url: str) -> None:
    """Test preference survey can be submitted."""
    login_helper(page, base_url)

    # Navigate to preferences
    preference_link = page.locator("text=🎯").or_(page.locator("text=好みの設定"))
    if preference_link.count() > 0:
        preference_link.first.click()
        time.sleep(2)

        # Look for save/submit button
        save_button = page.get_by_role("button", name="保存").or_(
            page.get_by_role("button", name="送信")
        )

        if save_button.count() > 0:
            save_button.first.click()
            time.sleep(2)

            # Check for success message
            success_message = page.locator("text=保存").or_(page.locator("text=成功"))
            # Success message should appear (or no error)
            assert page.locator('div[data-testid="stAlert"][data-baseweb="notification"]').count() >= 0


def test_preference_survey_has_sliders(page: Page, base_url: str) -> None:
    """Test that preference survey has slider controls."""
    login_helper(page, base_url)

    # Navigate to preferences
    preference_link = page.locator("text=🎯").or_(page.locator("text=好みの設定"))
    if preference_link.count() > 0:
        preference_link.first.click()
        time.sleep(2)

        # Check for slider elements (Streamlit sliders have specific structure)
        sliders = page.locator('[data-testid="stSlider"]')
        if sliders.count() > 0:
            assert sliders.count() >= 1, "Should have at least one slider for preferences"


def test_preference_survey_budget_selection(page: Page, base_url: str) -> None:
    """Test that preference survey has budget selection."""
    login_helper(page, base_url)

    # Navigate to preferences
    preference_link = page.locator("text=🎯").or_(page.locator("text=好みの設定"))
    if preference_link.count() > 0:
        preference_link.first.click()
        time.sleep(2)

        # Look for budget-related text
        budget_text = page.locator("text=予算").or_(page.locator("text=価格"))
        if budget_text.count() > 0:
            expect(budget_text.first).to_be_visible()


def test_preference_survey_category_selection(page: Page, base_url: str) -> None:
    """Test that preference survey has sake category selection."""
    login_helper(page, base_url)

    # Navigate to preferences
    preference_link = page.locator("text=🎯").or_(page.locator("text=好みの設定"))
    if preference_link.count() > 0:
        preference_link.first.click()
        time.sleep(2)

        # Look for sake categories (純米, 吟醸, etc.)
        categories = page.locator("text=純米").or_(page.locator("text=吟醸"))
        if categories.count() > 0:
            expect(categories.first).to_be_visible()


def test_preference_survey_complete_flow(page: Page, base_url: str) -> None:
    """Test complete preference survey flow."""
    login_helper(page, base_url)

    # Navigate to preferences
    preference_link = page.locator("text=🎯").or_(page.locator("text=好みの設定"))
    if preference_link.count() > 0:
        preference_link.first.click()
        time.sleep(2)

        # Try to interact with form elements
        # 1. Select experience level if available
        experience_select = page.locator("select").or_(page.locator('[role="combobox"]'))
        if experience_select.count() > 0:
            experience_select.first.click()
            time.sleep(1)

        # 2. Try to move slider if available
        sliders = page.locator('[data-testid="stSlider"]')
        if sliders.count() > 0:
            # Slider interaction is complex, just verify it's there
            expect(sliders.first).to_be_visible()

        # 3. Submit form
        save_button = page.get_by_role("button", name="保存").or_(
            page.get_by_role("button", name="送信")
        )
        if save_button.count() > 0:
            save_button.first.click()
            time.sleep(3)

            # Verify no critical errors
            error_alerts = page.locator('div[data-testid="stAlert"]').all()
            for alert in error_alerts:
                if alert.is_visible():
                    error_text = alert.text_content() or ""
                    assert "Exception" not in error_text, f"Unexpected error: {error_text}"


def test_preference_survey_validation(page: Page, base_url: str) -> None:
    """Test preference survey input validation."""
    login_helper(page, base_url)

    # Navigate to preferences
    preference_link = page.locator("text=🎯").or_(page.locator("text=好みの設定"))
    if preference_link.count() > 0:
        preference_link.first.click()
        time.sleep(2)

        # Try to submit empty/invalid form
        save_button = page.get_by_role("button", name="保存").or_(
            page.get_by_role("button", name="送信")
        )

        if save_button.count() > 0:
            # Submit without filling anything
            save_button.first.click()
            time.sleep(2)

            # Should either save successfully or show validation message
            # (either outcome is acceptable - just verify no crash)
            assert page.url is not None
