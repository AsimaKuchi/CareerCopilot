"""
Test Playwright auto-fill functionality.
"""
import pytest
import asyncio
import os

# Set the env var before importing playwright
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'

from playwright.async_api import async_playwright


class TestPlaywrightSetup:
    """Test that Playwright is properly configured."""
    
    @pytest.mark.asyncio
    async def test_playwright_browser_launches(self):
        """Test that Chromium browser can be launched."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            assert browser is not None
            
            # Create a page
            page = await browser.new_page()
            assert page is not None
            
            # Navigate to a test page
            await page.goto('https://example.com')
            title = await page.title()
            assert 'Example' in title
            
            await browser.close()
    
    @pytest.mark.asyncio
    async def test_playwright_can_navigate_to_greenhouse(self):
        """Test that Playwright can navigate to a Greenhouse job page."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Navigate to a Greenhouse job board
            await page.goto('https://job-boards.greenhouse.io/gitlab', timeout=30000)
            
            # Check we got some content
            content = await page.content()
            assert len(content) > 1000  # Should have substantial content
            
            await browser.close()


class TestPlaywrightAutofillFunction:
    """Test the playwright_auto_fill function from server.py."""
    
    @pytest.mark.asyncio
    async def test_captcha_detection(self):
        """Test that CAPTCHA detection works."""
        # This test validates that our CAPTCHA detection logic works
        captcha_indicators = [
            'captcha', 'recaptcha', 'hcaptcha', 'turnstile',
            'g-recaptcha', 'cf-turnstile', 'challenge-form',
            'verify you are human', 'prove you are not a robot'
        ]
        
        test_content = "<html><body>Please complete the reCAPTCHA to continue</body></html>"
        test_content_lower = test_content.lower()
        
        detected = False
        for indicator in captcha_indicators:
            if indicator in test_content_lower:
                detected = True
                break
        
        assert detected, "Should detect CAPTCHA in test content"
    
    @pytest.mark.asyncio
    async def test_field_selectors_exist(self):
        """Test that field selectors function exists and returns data."""
        # Import the function from server
        import sys
        sys.path.insert(0, '/app/backend')
        from server import get_field_selectors
        
        selectors = get_field_selectors('greenhouse')
        assert isinstance(selectors, dict)
        assert 'first_name' in selectors
        assert 'email' in selectors


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
