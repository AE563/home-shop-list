---
name: vanilla-js
description: Vanilla JavaScript expertise for this project. Use when writing or modifying static/js/ui.js, static/js/websocket.js, or any JavaScript that handles AJAX, DOM manipulation, event delegation, or WebSocket client logic. Activates for any frontend JS task.
---

# Vanilla JavaScript — Home Shop List

Ты пишешь чистый, идиоматичный ES6+ JavaScript без фреймворков. Логика разделена на два файла: `ui.js` (DOM и AJAX) и `websocket.js` (WS-клиент). Никаких новых зависимостей.

## Архитектура JS

```
static/js/
├── utils.js       -- Общие утилиты: window.shopUtils = { esc, fmtQty }
├── ui.js          -- Вся DOM-логика: accordion, CRUD-формы, AJAX-запросы
└── websocket.js   -- WebSocket клиент; использует DOM-билдеры из ui.js
```

**Правило:** `websocket.js` не знает про Django и не делает HTTP-запросы. `ui.js` не знает про WebSocket. Взаимодействие через глобальные функции, экспортируемые из `ui.js` в `window`.

`utils.js` подключается первым (до `ui.js` и `websocket.js`):
- `window.shopUtils.esc(str)` — экранирование HTML для безопасной вставки в `innerHTML`
- `window.shopUtils.fmtQty(qty)` — форматирование количества (убирает лишние нули: `2.00` → `2`)

---

## AJAX-запросы (fetch)

Все изменения данных идут через `fetch` с CSRF-токеном.

```javascript
// Получить CSRF-токен из cookie (Django стандарт)
function getCsrfToken() {
  return document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
}

// Универсальная обёртка для JSON-запросов
async function apiFetch(url, method, body = null) {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
  };
  if (body !== null) options.body = JSON.stringify(body);

  const response = await fetch(url, options);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return response.json();
}

// Использование
apiFetch(`/api/purchases/${id}/toggle/`, 'PATCH', { is_need_to_buy: false })
  .then(data => updatePurchaseInDOM(data.purchase))
  .catch(err => showInlineError(err.message));
```

---

## Event delegation

Никогда не вешай обработчики на динамически создаваемые элементы напрямую. Всегда используй делегирование на статический родитель.

```javascript
// НЕ ТАК -- элемент может быть создан динамически
document.querySelectorAll('.btn-delete-item').forEach(btn => {
  btn.addEventListener('click', handleDelete);
});

// ТАК -- делегирование на document или ближайший статический контейнер
document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn-delete-item');
  if (!btn) return;

  const purchaseId = btn.dataset.purchaseId;
  handleDeletePurchase(purchaseId);
});
```

### Паттерны кнопок в проекте

```
.btn-delete-item    [data-purchase-id]   -- удалить товар
.btn-edit-item      [data-purchase-id]   -- редактировать товар
.btn-save-item      [data-category-id]   -- сохранить товар
.btn-cancel-item    [data-category-id]   -- отмена формы товара
.btn-add-item       [data-category-id]   -- показать форму добавления товара
.btn-delete-cat     [data-category-id]   -- удалить категорию
.btn-edit-cat       [data-category-id]   -- редактировать категорию
.purchase-checkbox  [data-purchase-id]   -- переключить is_need_to_buy
```

---

## DOM-билдеры

Функции, создающие DOM-элементы из данных сервера. Должны быть доступны из `websocket.js`.

```javascript
// ui.js -- экспортируем в window для websocket.js
// Используй window.shopUtils.esc() для экранирования, shopUtils.fmtQty() для количества
window.buildPurchaseRow = function (purchase, showEditControls = false) {
  const div = document.createElement('div');
  div.className = 'd-flex align-items-center px-3 py-2 border-bottom';
  div.dataset.purchaseId = purchase.id;
  if (!purchase.is_need_to_buy) div.classList.add('opacity-50');

  const { esc, fmtQty } = window.shopUtils;
  div.innerHTML = `
    <div class="form-check me-3 mb-0">
      <input class="form-check-input purchase-checkbox"
             type="checkbox"
             ${purchase.is_need_to_buy ? 'checked' : ''}
             data-purchase-id="${purchase.id}">
    </div>
    <span class="flex-grow-1">
      ${esc(purchase.name)}
      <small class="text-muted ms-2">${fmtQty(purchase.quantity)} ${esc(purchase.unit_abbreviation)}</small>
    </span>
  `;
  return div;
};

window.buildCategorySection = function (category) {
  // Создаёт accordion-секцию для категории
  const div = document.createElement('div');
  div.className = 'accordion-item border-0 border-bottom';
  div.dataset.categoryId = category.id;
  // ... разметка
  return div;
};
```

---

## Оптимистичные обновления

Применяй изменения в DOM сразу, не дожидаясь ответа сервера. При ошибке — откатывай.

```javascript
async function togglePurchase(purchaseId, newValue) {
  const row = document.querySelector(`[data-purchase-id="${purchaseId}"]`);
  const checkbox = row?.querySelector('input[type=checkbox]');

  // Оптимистичное обновление
  if (checkbox) checkbox.checked = newValue;
  if (!newValue) row?.remove();   // убираем из просмотра мгновенно

  try {
    await apiFetch(`/api/purchases/${purchaseId}/toggle/`, 'PATCH', { is_need_to_buy: newValue });
  } catch (err) {
    // Откат: возвращаем чекбокс на место
    if (checkbox) checkbox.checked = !newValue;
    if (!newValue) {
      // TODO: вернуть строку в список
    }
    console.error('Toggle failed:', err.message);
  }
}
```

---

## Accordion (Bootstrap 5)

```javascript
// Свернуть / развернуть все категории
function toggleAll(collapse) {
  document.querySelectorAll('.accordion-collapse').forEach(el => {
    const instance = bootstrap.Collapse.getOrCreateInstance(el, { toggle: false });
    collapse ? instance.hide() : instance.show();
  });
  const btn = document.getElementById('toggleAllBtn');
  if (btn) btn.textContent = collapse ? 'Развернуть всё' : 'Свернуть всё';
}

// Показать/скрыть секцию категории по наличию товаров
function updateCategoryVisibility(categoryId) {
  const section = document.querySelector(`[data-category-id="${categoryId}"]`);
  if (!section) return;
  const items = section.querySelectorAll('[data-purchase-id]');
  section.style.display = items.length === 0 ? 'none' : '';
}
```

---

## Пустое состояние

```javascript
function updateEmptyState() {
  const hasItems = document.querySelectorAll('[data-purchase-id]').length > 0;
  const emptyState = document.getElementById('emptyState');
  if (emptyState) emptyState.style.display = hasItems ? 'none' : '';
}
```

---

## Inline-ошибки форм

```javascript
function showInlineError(formEl, message) {
  let errorEl = formEl.querySelector('.js-error');
  if (!errorEl) {
    errorEl = document.createElement('div');
    errorEl.className = 'js-error text-danger small mt-1';
    formEl.prepend(errorEl);
  }
  errorEl.textContent = message;
}

function clearInlineError(formEl) {
  formEl.querySelector('.js-error')?.remove();
}
```

---

## Валидация форм (клиентская)

```javascript
function validatePurchaseForm(name, quantity) {
  if (!name.trim()) return 'Введите название товара';
  if (parseFloat(quantity) <= 0 || isNaN(parseFloat(quantity))) {
    return 'Количество должно быть больше 0';
  }
  return null; // ок
}

function validateCategoryForm(name) {
  if (!name.trim()) return 'Введите название категории';
  return null;
}
```

---

## Правила

- **Никогда не используй `innerHTML` с пользовательскими данными** — только через `window.shopUtils.esc()` или `textContent`
- **Не используй `id` для динамических элементов** — используй `data-*` атрибуты и `querySelector`
- **Один обработчик события на тип действия** — используй делегирование, не навешивай обработчики в цикле
- **`async/await` вместо `.then().catch()` цепочек** — код читаемее
- **Не смешивай логику страниц** — `ui.js` должен корректно работать и на `/`, и на `/edit/`; используй проверку `document.getElementById('editPage')` для ветвления
- **Не используй `console.log` в продакшне** — только `console.error` для реальных ошибок

---

## Структура DOMContentLoaded

```javascript
// ui.js -- точка входа
document.addEventListener('DOMContentLoaded', function () {
  const isEditPage = document.body.dataset.page === 'edit';

  // Общая логика (обе страницы)
  initAccordion();
  initCheckboxToggle();

  // Только страница редактирования
  if (isEditPage) {
    initCategoryForms();
    initPurchaseForms();
  }
});
```
