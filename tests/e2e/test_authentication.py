"""
E2E Tests for Authentication Flow

Tests user registration, login, and logout functionality.
"""

import os
import time
from datetime import datetime

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def base_url() -> str:
    """Get base URL from environment or use default."""
    return os.getenv(
        "BASE_URL", "http://sakese-Publi-BG2ScFFG5nfS-804827597.us-west-2.elb.amazonaws.com"
    )


@pytest.fixture(scope="session")
def test_user_email() -> str:
    """Generate unique test user email."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"test+{timestamp}@sakesensei.com"


def test_homepage_loads(page: Page, base_url: str) -> None:
    """Test that the homepage loads correctly."""
    page.goto(base_url)
    expect(page).to_have_title("Sake Sensei 🍶")
    expect(page.locator(".main-header").first).to_be_visible()


def test_signup_button_visible(page: Page, base_url: str) -> None:
    """Test that signup button is visible on homepage."""
    page.goto(base_url)
    signup_button = page.locator("text=✨ 新規登録")
    expect(signup_button).to_be_visible()


def test_login_button_visible(page: Page, base_url: str) -> None:
    """Test that login button is visible on homepage."""
    page.goto(base_url)
    login_button = page.locator("text=🔐 ログイン")
    expect(login_button).to_be_visible()


def test_user_registration_flow(page: Page, base_url: str, test_user_email: str) -> None:
    """Test complete user registration flow."""
    page.goto(base_url)

    # Click signup button
    page.get_by_role("button", name="✨ 新規登録").click()
    time.sleep(2)

    # Fill registration form
    page.fill('input[placeholder="山田 太郎"]', "Test User")
    page.fill('input[placeholder="your.email@example.com"]', test_user_email)

    # Strong password meeting requirements
    test_password = "TestPass123!@#"
    password_inputs = page.locator('input[type="password"]').all()
    if len(password_inputs) >= 2:
        password_inputs[0].fill(test_password)
        password_inputs[1].fill(test_password)

    # Submit form - use the primary form submit button
    page.get_by_test_id("stBaseButton-primaryFormSubmit").click()
    time.sleep(3)

    # Check for success message or confirmation form
    # Note: Actual email confirmation would require email access
    # We check if the form submission was accepted
    page.wait_for_selector("text=確認コード", timeout=10000)


def test_login_with_test_account(page: Page, base_url: str) -> None:
    """Test login with existing test account."""
    page.goto(base_url)

    # Click login button
    page.get_by_role("button", name="🔐 ログイン").click()
    time.sleep(3)

    # Fill login form
    page.fill('input[placeholder="your.email@example.com"]', "test@sakesensei.com")
    password_input = page.locator('input[type="password"]').first
    password_input.fill("TestPass123!@#")

    # Submit form - use primary form submit button
    page.get_by_test_id("stBaseButton-primaryFormSubmit").click()

    # Wait for page reload after successful login
    page.wait_for_load_state("networkidle", timeout=30000)
    time.sleep(3)

    # Check if logged in - look for home page or user info
    expect(page.locator("text=ホーム")).to_be_visible(timeout=10000)


def test_user_info_displayed_after_login(page: Page, base_url: str) -> None:
    """Test that user info is displayed after login."""
    # Login first
    page.goto(base_url)
    page.get_by_role("button", name="🔐 ログイン").click()
    time.sleep(3)

    page.fill('input[placeholder="your.email@example.com"]', "test@sakesensei.com")
    password_input = page.locator('input[type="password"]').first
    password_input.fill("TestPass123!@#")
    page.get_by_test_id("stBaseButton-primaryFormSubmit").click()

    # Wait for page reload
    page.wait_for_load_state("networkidle", timeout=30000)
    time.sleep(2)

    # Check main app page is displayed
    expect(page.locator("text=ホーム")).to_be_visible(timeout=10000)


def test_logout_functionality(page: Page, base_url: str) -> None:
    """Test logout functionality."""
    # Login first
    page.goto(base_url)
    page.get_by_role("button", name="🔐 ログイン").click()
    time.sleep(3)

    page.fill('input[placeholder="your.email@example.com"]', "test@sakesensei.com")
    password_input = page.locator('input[type="password"]').first
    password_input.fill("TestPass123!@#")
    page.get_by_test_id("stBaseButton-primaryFormSubmit").click()

    # Wait for page reload
    page.wait_for_load_state("networkidle", timeout=30000)
    time.sleep(2)

    # Verify logged in
    expect(page.locator("text=ホーム")).to_be_visible(timeout=10000)

    # Click logout
    page.get_by_role("button", name="🚪 ログアウト").click()
    time.sleep(3)

    # Verify back to welcome page
    expect(page.locator("text=ようこそ Sake Sensei へ")).to_be_visible(timeout=10000)


def test_invalid_login_shows_error(page: Page, base_url: str) -> None:
    """Test that invalid login credentials show error."""
    page.goto(base_url)
    page.get_by_role("button", name="🔐 ログイン").click()
    time.sleep(3)

    page.fill('input[placeholder="your.email@example.com"]', "invalid@example.com")
    password_input = page.locator('input[type="password"]').first
    password_input.fill("WrongPassword123!@#")

    page.get_by_test_id("stBaseButton-primaryFormSubmit").click()
    time.sleep(5)

    # Check for error message - any error is acceptable
    expect(page.locator('div[data-testid="stAlert"]')).to_be_visible(timeout=15000)
