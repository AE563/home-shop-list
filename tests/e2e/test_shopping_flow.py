"""E2E tests (Selenium). Skeleton — to be expanded with view/edit page implementation."""

import pytest


@pytest.mark.skip(reason='Selenium not configured yet — implement after view/edit pages')
def test_uncheck_item_removes_it_from_view(browser, live_server, setup_data):
    """Снятие галочки с товара на странице просмотра удаляет его из списка."""
    from selenium.webdriver.common.by import By

    browser.get(f'{live_server.url}/')
    checkbox = browser.find_element(By.CSS_SELECTOR, "[data-purchase-id='1'] input[type=checkbox]")
    checkbox.click()

    items = browser.find_elements(By.CSS_SELECTOR, "[data-purchase-id='1']")
    assert len(items) == 0
