"""
Record a MealMap demo video with Playwright.

Prerequisites (run from the repo root, in two terminals):
    cd agents  && python server.py          # Flask API on :5001
    cd mealmap && npm run dev               # Vite on :5173

Then:
    pip install playwright && playwright install chromium
    python docs/record_demo.py                                   # dashboard walkthrough
    python docs/record_demo.py --ask "We have 500kg of tinned food in Cork. Which charities should get it?"
                                                                 # also shows the AI agent (needs AWS Bedrock creds)

Output: docs/raw-demo.webm  (convert with the ffmpeg commands in docs/README-assets.md)
"""
import argparse
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:5173/AWS-hackathon-food-redistribution-platform/"
OUT = Path(__file__).parent
W, H = 1440, 900

# Inline wordmark used only if the remote logo can't be fetched (e.g. offline recording)
FALLBACK_LOGO = """<svg xmlns='http://www.w3.org/2000/svg' width='160' height='40'>
<text x='0' y='29' font-family='Nunito,Arial,sans-serif' font-size='26' font-weight='800' fill='white'>MealMap</text></svg>"""


def smooth_scroll(page, to_y, steps=40, pause=18):
    start = page.evaluate("window.scrollY")
    for i in range(1, steps + 1):
        t = i / steps
        ease = t * t * (3 - 2 * t)  # smoothstep
        page.evaluate(f"window.scrollTo(0, {start + (to_y - start) * ease})")
        page.wait_for_timeout(pause)


def hover_path(page, selector, points=6, pause=450):
    """Move the mouse across a chart so Recharts tooltips appear."""
    box = page.locator(selector).first.bounding_box()
    if not box:
        return
    y = box["y"] + box["height"] * 0.55
    for i in range(points):
        x = box["x"] + box["width"] * (0.12 + 0.76 * i / max(points - 1, 1))
        page.mouse.move(x, y, steps=12)
        page.wait_for_timeout(pause)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ask", help="Question to send to the MealMap Intelligence agent")
    ap.add_argument("--offline-logo", action="store_true", help="Replace the remote logo with a text wordmark")
    ap.add_argument("--local-font", help="Path to a Nunito .woff2 to use if Google Fonts is unreachable")
    args = ap.parse_args()

    tmp = OUT / "_video_tmp"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=1,
            record_video_dir=str(tmp),
            record_video_size={"width": W, "height": H},
        )
        page = ctx.new_page()
        if args.offline_logo:
            page.route("**/*foodcloud*.svg", lambda r: r.fulfill(body=FALLBACK_LOGO, content_type="image/svg+xml"))

        if args.local_font:
            font_bytes = Path(args.local_font).read_bytes()
            css = "@font-face{font-family:'Nunito';font-weight:200 1000;src:url(https://local.font/nunito.woff2) format('woff2');}"
            page.route("https://fonts.googleapis.com/**", lambda r: r.fulfill(body=css, content_type="text/css"))
            page.route("https://local.font/**", lambda r: r.fulfill(body=font_bytes, content_type="font/woff2"))

        page.goto(URL)
        page.wait_for_selector(".recharts-surface", timeout=30000)
        page.wait_for_timeout(2200)  # title card moment

        # 1. Stock alerts: expand the panel
        page.locator(".alerts-header").click()
        page.wait_for_timeout(2600)
        alerts_bottom = page.evaluate("document.querySelector('.stock-alerts').getBoundingClientRect().bottom + scrollY")
        if alerts_bottom > H:
            smooth_scroll(page, alerts_bottom - H + 60)
            page.wait_for_timeout(1800)
        smooth_scroll(page, 0)
        page.locator(".alerts-header").click(force=True)  # collapse again
        page.wait_for_timeout(900)

        # 2. AI agent (only if asked, needs Bedrock)
        if args.ask:
            box = page.locator("input[placeholder*='Ask']").first
            box.click()
            box.type(args.ask, delay=35)
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")
            # wait for the agent answer (or error) to render
            page.wait_for_function(
                "!document.body.innerText.includes('Thinking') && !document.querySelector('button[disabled]')",
                timeout=120000,
            )
            page.wait_for_timeout(4500)
            ans_bottom = page.evaluate(
                "Math.max(...[...document.querySelectorAll('section, .card, div')].filter(e=>e.innerText.includes('MealMap Intelligence')).map(e=>e.getBoundingClientRect().bottom + scrollY))"
            )
            if ans_bottom > H:
                smooth_scroll(page, ans_bottom - H + 40, steps=70)
                page.wait_for_timeout(4000)

        # 3. Distribution analytics
        target = page.evaluate("[...document.querySelectorAll('h2')].find(h=>h.innerText.includes('Distribution Analytics')).getBoundingClientRect().top + scrollY - 24")
        smooth_scroll(page, target, steps=60)
        page.wait_for_timeout(1500)
        surfaces = page.locator(".recharts-wrapper")
        for i in range(surfaces.count()):
            el = surfaces.nth(i)
            el.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            hover_path(page, f".recharts-wrapper >> nth={i}")
        page.mouse.move(W - 10, 10, steps=10)
        page.wait_for_timeout(800)

        smooth_scroll(page, page.evaluate("document.body.scrollHeight") - H, steps=40)
        page.wait_for_timeout(1500)
        smooth_scroll(page, 0, steps=60)
        page.wait_for_timeout(1800)

        video_path = page.video.path()
        ctx.close()
        browser.close()

    final = OUT / "raw-demo.webm"
    shutil.move(video_path, final)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Saved {final}")


if __name__ == "__main__":
    main()
