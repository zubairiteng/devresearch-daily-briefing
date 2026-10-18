"""Local visible browser assistant using Playwright to pre-fill job application forms."""
import asyncio
import logging
from pathlib import Path
from typing import Optional
from database.models import JobItemModel
from .cv_parser import ParsedCVProfile

logger = logging.getLogger(__name__)


async def launch_browser_assist(
    job: JobItemModel,
    cv: ParsedCVProfile,
    cover_letter_text: str,
    cv_pdf_path: Optional[Path] = None
) -> bool:
    """Launches Playwright in a VISIBLE desktop window, navigates to the application page,

    and pre-fills common fields. NEVER SUBMITS. The user reviews and submits themselves.
    """
    from playwright.async_api import async_playwright

    target_url = job.apply_link or job.primary_url
    if target_url.startswith("mailto:"):
        logger.info("Target is mailto, browser assist not required.")
        return False

    try:
        pw = await async_playwright().start()
        # Launch visible browser on user's machine
        browser = await pw.chromium.launch(headless=False, slow_mo=50)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        logger.info(f"Opening visible application page: {target_url}")
        await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        # Attempt to pre-fill standard candidate fields safely
        try:
            # 1. Name fields
            for sel in ['input[name*="name" i]', 'input[id*="name" i]', 'input[placeholder*="name" i]']:
                if await page.is_visible(sel):
                    await page.fill(sel, cv.name)
                    break

            # 2. Email fields
            for sel in ['input[type="email"]', 'input[name*="email" i]', 'input[id*="email" i]']:
                if await page.is_visible(sel):
                    await page.fill(sel, cv.email)
                    break

            # 3. Phone fields
            for sel in ['input[type="tel"]', 'input[name*="phone" i]', 'input[id*="phone" i]']:
                if await page.is_visible(sel):
                    await page.fill(sel, cv.phone)
                    break

            # 4. Cover Letter textarea
            for sel in ['textarea[name*="cover" i]', 'textarea[id*="cover" i]', 'textarea[placeholder*="cover" i]', 'textarea']:
                if await page.is_visible(sel):
                    await page.fill(sel, cover_letter_text)
                    break

            # 5. Attach CV PDF if file input is available and cv_pdf_path exists
            if cv_pdf_path and cv_pdf_path.exists():
                file_inputs = page.locator('input[type="file"]')
                if await file_inputs.count() > 0:
                    try:
                        await file_inputs.first.set_input_files(str(cv_pdf_path))
                        logger.info(f"Attached tailored CV PDF: {cv_pdf_path.name}")
                    except Exception:
                        pass

        except Exception as fill_err:
            logger.debug(f"Non-critical form field matching note: {fill_err}")

        # Inject friendly review banner into the page
        await page.evaluate("""
            const banner = document.createElement('div');
            banner.style.position = 'fixed';
            banner.style.top = '10px';
            banner.style.left = '50%';
            banner.style.transform = 'translateX(-50%)';
            banner.style.backgroundColor = '#0f172a';
            banner.style.color = '#38bdf8';
            banner.style.border = '2px solid #0284c7';
            banner.style.padding = '12px 24px';
            banner.style.borderRadius = '10px';
            banner.style.zIndex = '999999';
            banner.style.fontSize = '14px';
            banner.style.fontWeight = 'bold';
            banner.style.boxShadow = '0 10px 25px rgba(0,0,0,0.4)';
            banner.innerHTML = 'DevResearch Apply Assistant: Form fields pre-filled from your CV. Please review, complete any verification, and click Submit when ready!';
            document.body.appendChild(banner);
        """)

        # Leave browser window open for user (do not close)
        return True

    except Exception as e:
        logger.error(f"Browser assist encountered an issue: {e}")
        return False
