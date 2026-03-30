import random
from typing import Dict
from playwright.sync_api import Page, BrowserContext

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
]

def random_user_agent() -> str:
    """Return a realistic, commonly used User-Agent string."""
    return random.choice(USER_AGENTS)

def apply_stealth(page: Page) -> None:
    """
    Patch generic JS variables that indicate a bot environment.
    Note: if `playwright-stealth` is used elsewhere, this serves as an additional layer.
    """
    _apply_navigator_patch(page)
    spoof_canvas(page)

def _apply_navigator_patch(page: Page) -> None:
    """Remove webdriver flag and add mock plugins."""
    stealth_js = """
    // Overwrite the `webdriver` property to return false
    Object.defineProperty(navigator, 'webdriver', {
        get: () => false,
    });
    
    // Mock navigator.plugins
    if (navigator.plugins.length === 0) {
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3],
        });
    }
    
    // Mock navigator.languages
    if (!navigator.languages || navigator.languages.length === 0) {
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
    }
    """
    page.add_init_script(stealth_js)

def spoof_canvas(page: Page) -> None:
    """Inject slight noise into canvas rendering to evade strict fingerprinting."""
    canvas_js = """
    const originalGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (type, contextAttributes) {
        const context = originalGetContext.call(this, type, contextAttributes);
        if (type === '2d' && context) {
            const originalFillText = context.fillText;
            context.fillText = function (...args) {
                // Add tiny imperceptible shift to text rendering to create a unique hash
                if (args.length >= 3) {
                    args[1] += (Math.random() * 0.001 - 0.0005);
                    args[2] += (Math.random() * 0.001 - 0.0005);
                }
                return originalFillText.apply(this, args);
            };
        }
        return context;
    };
    """
    page.add_init_script(canvas_js)

def set_realistic_headers(context: BrowserContext) -> None:
    """Set realistic baseline HTTP headers."""
    headers: Dict[str, str] = {
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    context.set_extra_http_headers(headers)
