---
name: bootstrap-mobile
description: Mobile-first Bootstrap 5 UI development targeting iPhone 15 (Safari). Use when building templates, layouts, components, or any HTML/CSS/JS UI for this project. Ensures touch-friendly, performant interfaces.
---

# Mobile-First Bootstrap 5 (iPhone 15 / Safari)

You build mobile-first interfaces with Bootstrap 5. Primary target: iPhone 15 (393x852pt logical viewport, Safari).

## Viewport and base HTML

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <!-- Critical: viewport must NOT set user-scalable=no (accessibility) -->
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Home Shop List</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
  {% block extra_css %}{% endblock %}
</head>
<body>
  {% block content %}{% endblock %}
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  {% block extra_js %}{% endblock %}
</body>
</html>
```

## Touch targets (Apple HIG)

Minimum touch target: **44x44pt**. Apply to all interactive elements:

```css
/* static/css/main.css */
.btn, .form-check-input, .list-group-item-action {
  min-height: 44px;
  min-width: 44px;
}

/* Checkbox -- default Bootstrap checkbox is too small for touch */
.form-check-input {
  width: 1.5em;
  height: 1.5em;
  margin-top: 0.1em;
  cursor: pointer;
}
```

## Header (fixed, doesn't overlap content)

```html
<header class="navbar navbar-light bg-white border-bottom fixed-top px-3">
  <div class="d-flex w-100 align-items-center justify-content-between gap-2">
    <!-- Page toggle -->
    <div class="btn-group btn-group-sm" role="group">
      <a href="{% url 'shop:view' %}"
         class="btn {% if page == 'view' %}btn-primary{% else %}btn-outline-primary{% endif %}">
        Просмотр
      </a>
      <a href="{% url 'shop:edit' %}"
         class="btn {% if page == 'edit' %}btn-primary{% else %}btn-outline-primary{% endif %}">
        Редактирование
      </a>
    </div>
    <!-- Collapse all / expand all -->
    <button id="toggleAllBtn" class="btn btn-sm btn-outline-secondary" type="button">
      Свернуть всё
    </button>
    <!-- Logout -->
    <a href="{% url 'users:logout' %}" class="btn btn-sm btn-link text-muted p-0">Выйти</a>
  </div>
</header>

<!-- Spacer so content isn't hidden under fixed header -->
<div style="height: 60px;"></div>
```

## Category accordion

```html
<div class="accordion" id="shopAccordion">
  {% for category in categories %}
  <div class="accordion-item border-0 border-bottom" data-category-id="{{ category.id }}">
    <h2 class="accordion-header">
      <button class="accordion-button py-3 fw-semibold"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#cat-{{ category.id }}"
              aria-expanded="true">
        {{ category.name }}
      </button>
    </h2>
    <div id="cat-{{ category.id }}"
         class="accordion-collapse collapse show"
         data-bs-parent="#shopAccordion">  {# Remove data-bs-parent for independent collapse #}
      <div class="accordion-body p-0">
        {% for item in category.visible_purchases %}
          {% include 'shop/_purchase_row.html' with item=item %}
        {% endfor %}
      </div>
    </div>
  </div>
  {% endfor %}
</div>
```

## Purchase row (partial: shop/_purchase_row.html)

```html
<div class="d-flex align-items-center px-3 py-2 border-bottom
            {% if not item.is_need_to_buy %}opacity-50{% endif %}"
     data-purchase-id="{{ item.id }}">
  <div class="form-check me-3 mb-0">
    <input class="form-check-input purchase-checkbox"
           type="checkbox"
           {% if item.is_need_to_buy %}checked{% endif %}
           data-purchase-id="{{ item.id }}"
           id="check-{{ item.id }}">
  </div>
  <label class="form-check-label flex-grow-1" for="check-{{ item.id }}">
    {{ item.name }}
    <small class="text-muted ms-2">{{ item.quantity }} {{ item.unit.abbreviation }}</small>
  </label>
  {% if show_edit_controls %}
  <div class="d-flex gap-1 ms-2">
    <button class="btn btn-sm btn-outline-secondary btn-edit-item p-1"
            data-purchase-id="{{ item.id }}">
      <i class="bi bi-pencil"></i>
    </button>
    <button class="btn btn-sm btn-outline-danger btn-delete-item p-1"
            data-purchase-id="{{ item.id }}">
      <i class="bi bi-trash"></i>
    </button>
  </div>
  {% endif %}
</div>
```

## Inline form (add / edit)

```html
<div class="px-3 py-2 bg-light" id="addItemForm-{{ category.id }}" style="display:none;">
  <div class="row g-2">
    <div class="col-12">
      <input type="text" class="form-control form-control-sm" placeholder="Название товара">
    </div>
    <div class="col-6">
      <input type="number" class="form-control form-control-sm" placeholder="Кол-во" min="0.01" step="0.01">
    </div>
    <div class="col-6">
      <select class="form-select form-select-sm">
        {% for unit in units %}
          <option value="{{ unit.id }}">{{ unit.abbreviation }}</option>
        {% endfor %}
      </select>
    </div>
    <div class="col-12 d-flex gap-2">
      <button class="btn btn-sm btn-success btn-save-item flex-grow-1">Сохранить</button>
      <button class="btn btn-sm btn-outline-secondary btn-cancel-item">Отмена</button>
    </div>
  </div>
</div>
```

## Empty state

```html
<div class="text-center text-muted py-5" id="emptyState">
  <p class="fs-5">Всё куплено!</p>
  <p>Список покупок пуст.</p>
</div>
```

## Error / banner

```html
<div id="connectionBanner"
     class="position-fixed bottom-0 start-0 end-0 bg-warning text-center py-2 small"
     style="display:none; z-index: 1050;">
  Соединение потеряно, переподключение...
</div>
```

## Collapse all / expand all (static/js/ui.js)

```javascript
document.getElementById('toggleAllBtn')?.addEventListener('click', function () {
  const isCollapsing = this.textContent.trim() === 'Свернуть всё';
  document.querySelectorAll('.accordion-collapse').forEach(el => {
    const bsCollapse = bootstrap.Collapse.getOrCreateInstance(el, { toggle: false });
    isCollapsing ? bsCollapse.hide() : bsCollapse.show();
  });
  this.textContent = isCollapsing ? 'Развернуть всё' : 'Свернуть всё';
});
```

## Safari-specific gotchas

- Safari does NOT support `overscroll-behavior` fully -- test scrolling manually
- `position: fixed` elements can jump when virtual keyboard opens -- keep header minimal
- `input[type=number]` on iOS shows numeric keyboard -- use `inputmode="decimal"` for fractional quantities
- Avoid `vh` units for full-height layouts -- use `dvh` or calculate manually (`window.innerHeight`)
- `gap` in flexbox works in Safari 14+ (iPhone 15 is fine)

## Naming convention for data attributes

```
data-purchase-id="42"      -- references a Purchase
data-category-id="7"       -- references a Category
data-action="toggle"       -- JS action identifier
```

Always use `data-*` attributes to pass server IDs to JavaScript. Never parse IDs from class names or text content.
