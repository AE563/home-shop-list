---
name: pytest-selenium
description: Senior QA engineer expertise with pytest-django and Selenium. Use when writing any tests: unit tests for models/views, integration tests for AJAX endpoints, WebSocket consumer tests, or end-to-end browser tests with Selenium. Activates automatically for any task involving tests, test files, conftest.py, or QA.
---

# Senior QA Engineer: pytest-django + Selenium

Ты — опытный QA-инженер. Пишешь чистые, изолированные, читаемые тесты. Следуешь принципу AAA: Arrange / Act / Assert.

## Структура тестовой директории

```
tests/
├── conftest.py              # общие фикстуры для всего проекта
├── test_models.py           # юнит-тесты моделей
├── test_views.py            # тесты Django views и AJAX-эндпоинтов
├── test_consumers.py        # тесты WebSocket-консьюмеров
└── e2e/
    ├── conftest.py          # фикстуры только для e2e (browser, live_server)
    └── test_shopping_flow.py
```

## pytest.ini

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## conftest.py (корневой)

```python
import pytest
from django.contrib.auth import get_user_model
from apps.shop.models import Category, Purchase, UnitOfMeasurement

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username='tester', password='pass123', email='tester@test.com')


@pytest.fixture
def client_auth(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def unit(db):
    return UnitOfMeasurement.objects.create(name='Штуки', abbreviation='шт.')


@pytest.fixture
def category(db):
    return Category.objects.create(name='Молочное', order=1)


@pytest.fixture
def purchase(db, category, unit):
    return Purchase.objects.create(
        name='Молоко',
        category=category,
        unit=unit,
        quantity=2,
        is_need_to_buy=True,
    )
```

## Юнит-тесты моделей (test_models.py)

```python
import pytest
from apps.shop.models import Category, Purchase


@pytest.mark.django_db
class TestCategoryOrdering:

    def test_new_category_takes_priority_and_shifts_others(self, unit):
        """При совпадении приоритета новая категория сдвигает существующие вниз."""
        cat_a = Category.objects.create(name='Молочное', order=1)
        cat_b = Category.objects.create(name='Овощи', order=2)

        Category.objects.create(name='Выпечка', order=1)  # конфликт с cat_a

        cat_a.refresh_from_db()
        cat_b.refresh_from_db()
        assert cat_a.order == 2
        assert cat_b.order == 3

    def test_category_str(self, category):
        assert str(category) == 'Молочное'


@pytest.mark.django_db
class TestPurchaseModel:

    def test_purchase_str_format(self, purchase, unit):
        assert str(purchase) == 'Молоко (2 шт.)'

    def test_is_need_to_buy_defaults_to_true(self, category, unit):
        item = Purchase.objects.create(name='Кефир', category=category, unit=unit, quantity=1)
        assert item.is_need_to_buy is True

    def test_quantity_must_be_positive(self, category, unit):
        """Количество <= 0 должно вызывать ValidationError."""
        from django.core.exceptions import ValidationError
        item = Purchase(name='Тест', category=category, unit=unit, quantity=0)
        with pytest.raises(ValidationError):
            item.full_clean()
```

## Тесты views и AJAX (test_views.py)

```python
import json
import pytest


@pytest.mark.django_db
class TestViewPageAccess:

    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get('/')
        assert response.status_code == 302
        assert '/login' in response['Location']

    def test_authenticated_user_sees_view_page(self, client_auth):
        response = client_auth.get('/')
        assert response.status_code == 200

    def test_only_needed_items_shown_on_view_page(self, client_auth, purchase, category, unit):
        from apps.shop.models import Purchase
        not_needed = Purchase.objects.create(
            name='Сыр', category=category, unit=unit,
            quantity=1, is_need_to_buy=False
        )
        response = client_auth.get('/')
        content = response.content.decode()
        assert 'Молоко' in content       # is_need_to_buy=True -- должен быть
        assert 'Сыр' not in content      # is_need_to_buy=False -- не должен быть


@pytest.mark.django_db
class TestTogglePurchaseAPI:

    def test_toggle_sets_is_need_to_buy_false(self, client_auth, purchase):
        response = client_auth.patch(
            f'/api/purchases/{purchase.pk}/toggle/',
            data=json.dumps({'is_need_to_buy': False}),
            content_type='application/json',
        )
        assert response.status_code == 200
        purchase.refresh_from_db()
        assert purchase.is_need_to_buy is False

    def test_toggle_returns_json(self, client_auth, purchase):
        response = client_auth.patch(
            f'/api/purchases/{purchase.pk}/toggle/',
            data=json.dumps({'is_need_to_buy': False}),
            content_type='application/json',
        )
        data = response.json()
        assert 'is_need_to_buy' in data

    def test_toggle_requires_auth(self, client, purchase):
        response = client.patch(f'/api/purchases/{purchase.pk}/toggle/')
        assert response.status_code in (302, 401, 403)


@pytest.mark.django_db
class TestCategoryAPI:

    def test_create_category(self, client_auth):
        response = client_auth.post(
            '/api/categories/',
            data=json.dumps({'name': 'Фрукты', 'order': 1}),
            content_type='application/json',
        )
        assert response.status_code == 201

    def test_delete_category_cascades_purchases(self, client_auth, category, purchase):
        from apps.shop.models import Purchase
        client_auth.delete(f'/api/categories/{category.pk}/')
        assert not Purchase.objects.filter(pk=purchase.pk).exists()
```

## Тесты WebSocket-консьюмера (test_consumers.py)

```python
import pytest
import json
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
from config.asgi import application


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestShopConsumer:

    async def test_authenticated_user_can_connect(self, user):
        communicator = WebsocketCommunicator(application, '/ws/shop/')
        communicator.scope['user'] = user
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_unauthenticated_user_is_rejected(self):
        from django.contrib.auth.models import AnonymousUser
        communicator = WebsocketCommunicator(application, '/ws/shop/')
        communicator.scope['user'] = AnonymousUser()
        connected, code = await communicator.connect()
        assert not connected

    async def test_receives_broadcast_after_purchase_update(self, user, purchase):
        communicator = WebsocketCommunicator(application, '/ws/shop/')
        communicator.scope['user'] = user
        await communicator.connect()

        # Имитируем broadcast через channel layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            'shop',
            {
                'type': 'shop.update',
                'payload': {'type': 'purchase.updated', 'purchase_id': purchase.pk, 'is_need_to_buy': False},
            }
        )

        message = await communicator.receive_json_from(timeout=3)
        assert message['type'] == 'purchase.updated'
        assert message['purchase_id'] == purchase.pk
        await communicator.disconnect()
```

## E2E-тесты Selenium (e2e/conftest.py)

```python
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@pytest.fixture(scope='session')
def browser():
    """Headless Chrome для e2e-тестов."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=393,852')  # iPhone 15 logical viewport

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)  # секунд ожидания элементов
    yield driver
    driver.quit()


@pytest.fixture
def logged_in_browser(browser, live_server, user):
    """Браузер с уже выполненным входом."""
    browser.get(f'{live_server.url}/login')

    browser.find_element('name', 'username').send_keys('tester')
    browser.find_element('name', 'password').send_keys('pass123')
    browser.find_element('css selector', 'button[type=submit]').click()

    # Ждём редиректа на главную
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By
    WebDriverWait(browser, 5).until(EC.url_to_be(f'{live_server.url}/'))
    return browser
```

## E2E-тесты Selenium (e2e/test_shopping_flow.py)

```python
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.mark.django_db(transaction=True)
class TestShoppingFlow:

    def test_uncheck_item_removes_from_view(self, logged_in_browser, purchase):
        browser = logged_in_browser

        # Товар виден на странице просмотра
        item_row = browser.find_element(By.CSS_SELECTOR, f'[data-purchase-id="{purchase.pk}"]')
        assert item_row.is_displayed()

        # Снимаем галочку
        checkbox = item_row.find_element(By.CSS_SELECTOR, 'input[type=checkbox]')
        checkbox.click()

        # Ждём исчезновения товара
        WebDriverWait(browser, 3).until(
            EC.staleness_of(item_row)
        )

        # Убеждаемся что элемента нет в DOM
        remaining = browser.find_elements(By.CSS_SELECTOR, f'[data-purchase-id="{purchase.pk}"]')
        assert len(remaining) == 0

    def test_empty_state_shown_when_list_is_empty(self, logged_in_browser):
        browser = logged_in_browser
        empty = browser.find_element(By.ID, 'emptyState')
        assert empty.is_displayed()

    def test_login_page_redirects_to_view_page(self, browser, live_server, user):
        browser.get(f'{live_server.url}/login')
        browser.find_element('name', 'username').send_keys('tester')
        browser.find_element('name', 'password').send_keys('pass123')
        browser.find_element('css selector', 'button[type=submit]').click()

        WebDriverWait(browser, 5).until(
            EC.url_to_be(f'{live_server.url}/')
        )
        assert browser.current_url == f'{live_server.url}/'
```

## Правила написания тестов

- **Один тест — одно утверждение** (или несколько связанных, но про одно поведение)
- **Имя теста — описание поведения**: `test_uncheck_item_removes_from_view`, не `test_item_1`
- **Arrange / Act / Assert** — явно разделяй подготовку, действие и проверку
- **Не тестируй Django** — тестируй свою логику. Не проверяй что `CharField` сохраняет строку
- **Используй фикстуры** из `conftest.py`, не создавай объекты прямо в тестах
- **`@pytest.mark.django_db`** обязателен для любого теста, трогающего БД
- **`transaction=True`** нужен для тестов с WebSocket (Channels) и Selenium (async)
- **Selenium: используй явные ожидания** (`WebDriverWait`) вместо `time.sleep()`
- **Не забывай `await communicator.disconnect()`** в async-тестах, иначе утечка соединений

## Запуск тестов

```bash
# Все тесты
pytest

# Только юнит-тесты (без e2e)
pytest tests/ --ignore=tests/e2e/

# Только e2e
pytest tests/e2e/

# Конкретный файл
pytest tests/test_models.py

# С покрытием
pytest --cov=apps --cov-report=term-missing

# Только упавшие тесты (повторный запуск)
pytest --lf
```

## Зависимости (добавить в requirements.txt)

```
pytest
pytest-django
pytest-asyncio
pytest-cov
channels[daphne]
selenium
```
