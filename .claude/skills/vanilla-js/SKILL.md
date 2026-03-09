---
name: vanilla-js
description: Vanilla JavaScript expertise for this project. Use when writing or modifying static/js/ui.js, static/js/websocket.js, or any JavaScript that handles AJAX, DOM manipulation, event delegation, or WebSocket client logic. Activates for any frontend JS task.
---

# Vanilla JS — решения этого проекта

---

## Контракт между тремя файлами

Порядок загрузки в шаблоне фиксирован: `utils.js` → `ui.js` → `websocket.js`.

| Файл | Экспортирует в `window` | Импортирует из `window` |
|------|------------------------|------------------------|
| `utils.js` | `shopUtils.esc`, `shopUtils.fmtQty` | — |
| `ui.js` | DOM-билдеры: `buildPurchaseRow`, `buildCategorySection`, ... | `shopUtils` |
| `websocket.js` | — | `shopUtils`, DOM-билдеры из `ui.js` |

`websocket.js` не делает HTTP-запросы. `ui.js` не знает про WebSocket.

---

## `window.shopUtils`

```js
// Всегда используй вместо самодельных функций:
const { esc, fmtQty } = window.shopUtils;

esc(purchase.name)            // экранирование для innerHTML
fmtQty(purchase.quantity)     // '2.00' → '2', '1.50' → '1.5'
```

**Никогда** не пиши свою `escapeHtml` — дублирование.

---

## Event delegation — единственный паттерн навески обработчиков

```js
// НЕ ТАК — элементы динамические, обработчик не сработает после WS-вставки
document.querySelectorAll('.btn-delete-item').forEach(btn => ...);

// ТАК — один обработчик на статический контейнер
document.addEventListener('click', function(e) {
    const btn = e.target.closest('.btn-delete-item');
    if (!btn) return;
    handleDeletePurchase(btn.dataset.purchaseId);
});
```

---

## Кнопки и data-атрибуты (полный список)

```
.purchase-checkbox   [data-purchase-id]   — toggle is_need_to_buy
.btn-edit-item       [data-purchase-id]   — открыть форму редактирования
.btn-delete-item     [data-purchase-id]   — удалить товар
.btn-save-item       [data-category-id]   — сохранить товар
.btn-cancel-item     [data-category-id]   — скрыть форму
.btn-add-item        [data-category-id]   — показать форму добавления
.btn-edit-cat        [data-category-id]   — редактировать категорию
.btn-delete-cat      [data-category-id]   — удалить категорию
```

ID никогда не парсить из текста или классов — только `dataset.*`.

---

## WS события → DOM функции

```js
'purchase.created' → buildPurchaseRow(data.purchase) + вставить в секцию
'purchase.updated' → обновить строку или удалить если !is_need_to_buy (на view-странице)
'purchase.deleted' → удалить [data-purchase-id=X]
'category.created' → buildCategorySection(data.category) + вставить
'category.updated' → обновить заголовок [data-category-id=X]
'category.deleted' → удалить [data-category-id=X] со всеми товарами
```

---

## Запрещено

- **`innerHTML` с пользовательскими данными без `esc()`** — XSS
- **Обработчики в цикле** на динамических элементах — только delegation
- **`id` для динамических элементов** — только `data-*` + querySelector
- **`console.log` в продакшне** — только `console.error` для реальных ошибок
- **Новые зависимости** — проект на Vanilla JS, никаких npm-пакетов в рантайм
