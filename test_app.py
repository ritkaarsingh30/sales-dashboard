from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8501")
        # Just taking a screenshot to see if it loads successfully without failing
        page.wait_for_timeout(5000) # give streamlit time to load
        page.screenshot(path="dashboard_load.png")
        browser.close()

if __name__ == "__main__":
    run()
