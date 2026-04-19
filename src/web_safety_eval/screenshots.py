from __future__ import annotations

import asyncio
from pathlib import Path


def capture_html_screenshot(html: str, out_path: Path, title: str | None = None) -> bool:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return False

    async def _run() -> bool:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1280, "height": 900})
            await page.set_content(html, wait_until="load")
            if title:
                await page.evaluate(
                    "(t) => { document.title = t; }",
                    title,
                )
            await page.screenshot(path=str(out_path), full_page=True)
            await browser.close()
        return True

    try:
        return asyncio.run(_run())
    except Exception:
        return False
