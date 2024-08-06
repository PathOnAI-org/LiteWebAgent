from playwright.sync_api import sync_playwright


class PlaywrightManager:
    def __init__(self, storage_state=None):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.storage_state = storage_state

    def initialize(self):
        if self.playwright is None:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=False)

            # Use the storage_state if provided
            if self.storage_state:
                self.context = self.browser.new_context(storage_state=self.storage_state)
            else:
                self.context = self.browser.new_context()

            self.page = self.context.new_page()

    def get_browser(self):
        if self.browser is None:
            self.initialize()
        return self.browser

    def get_context(self):
        if self.context is None:
            self.initialize()
        return self.context

    def get_page(self):
        if self.page is None:
            self.initialize()
        return self.page

    def close(self):
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None


# Initialize the PlaywrightManager with the storage state
playwright_manager = PlaywrightManager(storage_state='ai_agent/playground/state.json')


def get_browser():
    return playwright_manager.get_browser()


def get_context():
    return playwright_manager.get_context()


def get_page():
    return playwright_manager.get_page()


def close_playwright():
    playwright_manager.close()