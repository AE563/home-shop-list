/**
 * ui.js — DOM manipulation: accordion, collapse-all/expand-all,
 *          checkbox toggle, edit-page CRUD.
 * Covers: FR-04 to FR-17
 */

'use strict';

// -----------------------------------------------------------------------
// CSRF token helper
// -----------------------------------------------------------------------
function getCookie(name) {
    var value = '; ' + document.cookie;
    var parts = value.split('; ' + name + '=');
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
}

// -----------------------------------------------------------------------
// Accordion: toggle a single category's purchase list (FR-16)
// Skips click when the target is an action button inside the header.
// -----------------------------------------------------------------------
document.addEventListener('click', function (e) {
    var header = e.target.closest('.category-header');
    if (!header) return;
    if (e.target.closest('button')) return;  // edit / delete inside header

    var block = header.closest('.category-block');
    var body = block && block.querySelector('.category-body');
    if (!body) return;

    var isHidden = body.style.display === 'none';
    body.style.display = isHidden ? '' : 'none';
    var icon = header.querySelector('.collapse-icon');
    if (icon) icon.classList.toggle('bi-chevron-down', isHidden);
    if (icon) icon.classList.toggle('bi-chevron-up', !isHidden);
    updateToggleAllButton();
});

// -----------------------------------------------------------------------
// Collapse-all / Expand-all (FR-17)
// -----------------------------------------------------------------------
var btnToggleAll = document.getElementById('btn-toggle-all');
if (btnToggleAll) {
    btnToggleAll.addEventListener('click', function () {
        var bodies = document.querySelectorAll('.category-body');
        var anyVisible = Array.from(bodies).some(function (b) { return b.style.display !== 'none'; });
        bodies.forEach(function (b) { b.style.display = anyVisible ? 'none' : ''; });
        updateToggleAllButton();
    });
}

function updateToggleAllButton() {
    var btn = document.getElementById('btn-toggle-all');
    if (!btn) return;
    var bodies = document.querySelectorAll('.category-body');
    var anyVisible = Array.from(bodies).some(function (b) { return b.style.display !== 'none'; });
    btn.textContent = anyVisible ? 'Свернуть всё' : 'Развернуть всё';
}

// -----------------------------------------------------------------------
// Checkbox toggle: AJAX PATCH + optimistic DOM update (FR-15)
// -----------------------------------------------------------------------
document.addEventListener('change', function (e) {
    var cb = e.target;
    if (!cb.classList.contains('toggle-checkbox')) return;

    var pk = cb.dataset.purchaseId;
    var isNeedToBuy = cb.checked;
    var isViewPage = !!document.getElementById('shop-view');

    if (isViewPage && !isNeedToBuy) {
        removePurchaseFromView(pk);
    } else if (!isViewPage) {
        var item = cb.closest('.purchase-item');
        if (item) item.classList.toggle('is-bought', !isNeedToBuy);
    }

    fetch('/api/purchases/' + pk + '/toggle/', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ is_need_to_buy: isNeedToBuy }),
    }).catch(function () { location.reload(); });
});

function removePurchaseFromView(pk) {
    var item = document.querySelector('[data-purchase-id="' + pk + '"]');
    if (!item) return;
    var block = item.closest('.category-block');
    item.remove();
    if (block && !block.querySelector('.purchase-item')) block.remove();
    var view = document.getElementById('shop-view');
    if (view && !view.querySelector('.category-block')) {
        var p = document.createElement('p');
        p.id = 'empty-state';
        p.className = 'text-muted text-center mt-5';
        p.textContent = 'Всё куплено! Список покупок пуст.';
        view.appendChild(p);
    }
}

// -----------------------------------------------------------------------
// Edit page (FR-04 to FR-14) — active only on /edit
// -----------------------------------------------------------------------
(function () {
    if (!document.getElementById('shop-edit')) return;

    // --- Utilities ---

    function api(url, method, body) {
        return fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: body !== undefined ? JSON.stringify(body) : undefined,
        }).then(function (r) {
            return r.json().then(function (d) {
                if (!r.ok) throw new Error(d.error || 'Ошибка сервера');
                return d;
            });
        });
    }

    // Build <option> tags from the hidden #units-ref select
    function unitsHtml(selectedId) {
        var ref = document.getElementById('units-ref');
        if (!ref) return '';
        return Array.from(ref.options).map(function (o) {
            return '<option value="' + window.shopUtils.esc(o.value) + '"' +
                (String(o.value) === String(selectedId) ? ' selected' : '') +
                '>' + window.shopUtils.esc(o.text) + '</option>';
        }).join('');
    }

    function showErr(inputEl, errEl, msg) {
        inputEl.classList.add('is-invalid');
        if (errEl) errEl.textContent = msg;
    }

    function clearErr(inputEl) { inputEl.classList.remove('is-invalid'); }

    // -----------------------------------------------------------------------
    // Add category button / form (FR-04, FR-05)
    // -----------------------------------------------------------------------
    document.getElementById('btn-add-category').addEventListener('click', function () {
        var form = document.getElementById('new-category-form');
        form.style.display = form.style.display === 'none' ? '' : 'none';
        if (form.style.display !== 'none') document.getElementById('new-cat-name').focus();
    });

    document.getElementById('btn-cancel-category').addEventListener('click', function () {
        document.getElementById('new-category-form').style.display = 'none';
        resetNewCatForm();
    });

    document.getElementById('btn-save-category').addEventListener('click', function () {
        var nameEl = document.getElementById('new-cat-name');
        var errEl  = document.getElementById('new-cat-name-error');
        var name   = nameEl.value.trim();
        var order  = parseInt(document.getElementById('new-cat-order').value) || 1;

        if (!name) { showErr(nameEl, errEl, 'Введите название категории.'); return; }
        clearErr(nameEl);

        api('/api/categories/', 'POST', { name: name, order: order })
            .then(function (data) {
                document.getElementById('new-category-form').style.display = 'none';
                resetNewCatForm();
                var noMsg = document.getElementById('no-categories-msg');
                if (noMsg) noMsg.remove();
                // Guard: WS may have already inserted this block before the HTTP response arrived
                if (!document.querySelector('#shop-edit .category-block[data-category-id="' + data.category.id + '"]')) {
                    var anchor = document.getElementById('new-category-form');
                    anchor.parentNode.insertBefore(buildCategoryBlock(data.category), anchor.nextSibling);
                }
            })
            .catch(function (err) { showErr(nameEl, errEl, err.message); });
    });

    function resetNewCatForm() {
        document.getElementById('new-cat-name').value = '';
        clearErr(document.getElementById('new-cat-name'));
        document.getElementById('new-cat-order').value = '1';
    }

    // -----------------------------------------------------------------------
    // Event delegation for all dynamic edit-page interactions
    // -----------------------------------------------------------------------
    document.addEventListener('click', function (e) {
        if (!document.getElementById('shop-edit')) return;

        var btn;

        // ── Edit category ──
        btn = e.target.closest('.btn-edit-category');
        if (btn) {
            e.stopPropagation();
            var block = document.querySelector('.category-block[data-category-id="' + btn.dataset.categoryId + '"]');
            if (!block) return;
            block.querySelector('.category-header').style.display = 'none';
            block.querySelector('.category-edit-form').style.display = '';
            block.querySelector('.edit-cat-name').focus();
            return;
        }

        // ── Cancel category edit ──
        btn = e.target.closest('.btn-cancel-edit-category');
        if (btn) {
            var block = btn.closest('.category-block');
            block.querySelector('.category-header').style.display = '';
            block.querySelector('.category-edit-form').style.display = 'none';
            return;
        }

        // ── Save category edit ──
        btn = e.target.closest('.btn-save-edit-category');
        if (btn) {
            var block  = btn.closest('.category-block');
            var nameEl = block.querySelector('.edit-cat-name');
            var errEl  = block.querySelector('.edit-cat-name-error');
            var name   = nameEl.value.trim();
            var order  = parseInt(block.querySelector('.edit-cat-order').value) || 1;
            var pk     = btn.dataset.categoryId;

            if (!name) { showErr(nameEl, errEl, 'Введите название категории.'); return; }
            clearErr(nameEl);

            api('/api/categories/' + pk + '/', 'PATCH', { name: name, order: order })
                .then(function (data) {
                    var cat = data.category;
                    block.querySelector('.category-name-display').textContent = cat.name;
                    var pb = block.querySelector('.priority-badge');
                    if (pb) pb.textContent = 'приоритет: ' + cat.order;
                    nameEl.value = cat.name;
                    block.querySelector('.edit-cat-order').value = cat.order;
                    var delBtn = block.querySelector('.btn-delete-category');
                    if (delBtn) delBtn.dataset.categoryName = cat.name;
                    block.querySelector('.category-header').style.display = '';
                    block.querySelector('.category-edit-form').style.display = 'none';
                })
                .catch(function (err) { showErr(nameEl, errEl, err.message); });
            return;
        }

        // ── Delete category ──
        btn = e.target.closest('.btn-delete-category');
        if (btn) {
            e.stopPropagation();
            var count = parseInt(btn.dataset.purchaseCount) || 0;
            var msg = count > 0
                ? 'Будут удалены ' + count + ' товар(ов). Продолжить?'
                : 'Удалить категорию «' + btn.dataset.categoryName + '»?';
            if (!confirm(msg)) return;
            var pk = btn.dataset.categoryId;
            api('/api/categories/' + pk + '/', 'DELETE')
                .then(function () {
                    var block = document.querySelector('.category-block[data-category-id="' + pk + '"]');
                    if (block) block.remove();
                    if (!document.querySelector('.category-block')) {
                        var p = document.createElement('p');
                        p.id = 'no-categories-msg';
                        p.className = 'text-muted text-center mt-5';
                        p.textContent = 'Нет категорий. Добавьте первую!';
                        document.getElementById('shop-edit').appendChild(p);
                    }
                })
                .catch(function (err) { alert(err.message); });
            return;
        }

        // ── Add purchase: show form ──
        btn = e.target.closest('.btn-add-purchase');
        if (btn) {
            var wrap = btn.closest('.add-purchase-wrap');
            btn.style.display = 'none';
            wrap.querySelector('.new-purchase-form').style.display = '';
            wrap.querySelector('.new-purchase-name').focus();
            return;
        }

        // ── Cancel new purchase ──
        btn = e.target.closest('.btn-cancel-new-purchase');
        if (btn) {
            var wrap   = btn.closest('.add-purchase-wrap');
            var nameEl = wrap.querySelector('.new-purchase-name');
            wrap.querySelector('.new-purchase-form').style.display = 'none';
            wrap.querySelector('.btn-add-purchase').style.display = '';
            nameEl.value = '';
            clearErr(nameEl);
            return;
        }

        // ── Save new purchase ──
        btn = e.target.closest('.btn-save-new-purchase');
        if (btn) {
            var wrap       = btn.closest('.add-purchase-wrap');
            var nameEl     = wrap.querySelector('.new-purchase-name');
            var errEl      = wrap.querySelector('.new-purchase-name-error');
            var name       = nameEl.value.trim();
            var quantity   = parseFloat(wrap.querySelector('.new-purchase-quantity').value);
            var unitId     = wrap.querySelector('.new-purchase-unit').value;
            var categoryId = btn.dataset.categoryId;

            if (!name) { showErr(nameEl, errEl, 'Введите название товара.'); return; }
            if (!quantity || quantity <= 0) { return; }
            clearErr(nameEl);

            api('/api/purchases/', 'POST', { name: name, quantity: quantity, unit_id: unitId, category_id: categoryId })
                .then(function (data) {
                    wrap.querySelector('.new-purchase-form').style.display = 'none';
                    wrap.querySelector('.btn-add-purchase').style.display = '';
                    nameEl.value = '';
                    // Guard: WS may have already inserted this item before the HTTP response arrived
                    if (!document.querySelector('#shop-edit .purchase-item[data-purchase-id="' + data.purchase.id + '"]')) {
                        var block  = wrap.closest('.category-block');
                        var delBtn = block && block.querySelector('.btn-delete-category');
                        if (delBtn) delBtn.dataset.purchaseCount = parseInt(delBtn.dataset.purchaseCount || 0) + 1;
                        wrap.parentNode.insertBefore(buildPurchaseItem(data.purchase), wrap);
                    }
                })
                .catch(function (err) { showErr(nameEl, errEl, err.message); });
            return;
        }

        // ── Edit purchase: show form ──
        btn = e.target.closest('.btn-edit-purchase');
        if (btn) {
            var item = btn.closest('.purchase-item');
            item.querySelector('.purchase-display').style.display = 'none';
            item.querySelector('.purchase-edit-form').style.display = '';
            item.querySelector('.edit-purchase-name').focus();
            return;
        }

        // ── Cancel purchase edit ──
        btn = e.target.closest('.btn-cancel-edit-purchase');
        if (btn) {
            var item = btn.closest('.purchase-item');
            item.querySelector('.purchase-display').style.display = '';
            item.querySelector('.purchase-edit-form').style.display = 'none';
            return;
        }

        // ── Save purchase edit ──
        btn = e.target.closest('.btn-save-edit-purchase');
        if (btn) {
            var item     = btn.closest('.purchase-item');
            var nameEl   = item.querySelector('.edit-purchase-name');
            var errEl    = item.querySelector('.edit-purchase-name-error');
            var name     = nameEl.value.trim();
            var quantity = parseFloat(item.querySelector('.edit-purchase-quantity').value);
            var unitId   = item.querySelector('.edit-purchase-unit').value;
            var pk       = btn.dataset.purchaseId;

            if (!name) { showErr(nameEl, errEl, 'Введите название товара.'); return; }
            if (!quantity || quantity <= 0) { return; }
            clearErr(nameEl);

            api('/api/purchases/' + pk + '/', 'PATCH', { name: name, quantity: quantity, unit_id: unitId })
                .then(function (data) {
                    var p = data.purchase;
                    item.querySelector('.purchase-display .flex-grow-1').textContent =
                        p.name + ' — ' + window.shopUtils.fmtQty(p.quantity) + ' ' + p.unit_abbreviation;
                    nameEl.value = p.name;
                    item.querySelector('.edit-purchase-quantity').value = p.quantity;
                    item.querySelector('.purchase-display').style.display = '';
                    item.querySelector('.purchase-edit-form').style.display = 'none';
                })
                .catch(function (err) { showErr(nameEl, errEl, err.message); });
            return;
        }

        // ── Delete purchase ──
        btn = e.target.closest('.btn-delete-purchase');
        if (btn) {
            var pk = btn.dataset.purchaseId;
            api('/api/purchases/' + pk + '/', 'DELETE')
                .then(function () {
                    var item   = document.querySelector('.purchase-item[data-purchase-id="' + pk + '"]');
                    if (!item) return;
                    var block  = item.closest('.category-block');
                    item.remove();
                    if (block) {
                        var delBtn = block.querySelector('.btn-delete-category');
                        if (delBtn) {
                            var cnt = parseInt(delBtn.dataset.purchaseCount) || 0;
                            delBtn.dataset.purchaseCount = Math.max(0, cnt - 1);
                        }
                    }
                })
                .catch(function (err) { alert(err.message); });
            return;
        }
    });

    // -----------------------------------------------------------------------
    // DOM builders (for dynamically inserted elements)
    // -----------------------------------------------------------------------

    function buildCategoryBlock(cat) {
        var div = document.createElement('div');
        div.className = 'category-block mb-2';
        div.dataset.categoryId = cat.id;
        div.innerHTML =
            '<div class="category-header">' +
            '  <div class="d-flex align-items-center gap-2 overflow-hidden">' +
            '    <i class="bi bi-chevron-down collapse-icon"></i>' +
            '    <div class="overflow-hidden">' +
            '      <div class="fw-semibold text-truncate category-name-display">' + window.shopUtils.esc(cat.name) + '</div>' +
            '      <div class="priority-badge">приоритет: ' + cat.order + '</div>' +
            '    </div>' +
            '  </div>' +
            '  <div class="d-flex gap-1 flex-shrink-0 ms-2">' +
            '    <button class="btn btn-sm btn-link p-1 text-secondary btn-edit-category" data-category-id="' + cat.id + '"><i class="bi bi-pencil-square"></i></button>' +
            '    <button class="btn btn-sm btn-link p-1 text-danger btn-delete-category"' +
            '      data-category-id="' + cat.id + '" data-category-name="' + window.shopUtils.esc(cat.name) + '" data-purchase-count="0"><i class="bi bi-trash3"></i></button>' +
            '  </div>' +
            '</div>' +
            '<div class="category-edit-form card border-primary mb-1" style="display:none;">' +
            '  <div class="card-body py-2">' +
            '    <div class="row g-2 align-items-end">' +
            '      <div class="col-8"><label class="form-label mb-1 small">Название</label>' +
            '        <input type="text" class="edit-cat-name form-control form-control-sm" value="' + window.shopUtils.esc(cat.name) + '">' +
            '        <div class="invalid-feedback edit-cat-name-error"></div></div>' +
            '      <div class="col-4"><label class="form-label mb-1 small">Приоритет</label>' +
            '        <input type="number" class="edit-cat-order form-control form-control-sm" value="' + cat.order + '" min="1"></div>' +
            '    </div>' +
            '    <div class="mt-2 d-flex gap-2">' +
            '      <button class="btn btn-primary btn-sm btn-save-edit-category" data-category-id="' + cat.id + '">Сохранить</button>' +
            '      <button class="btn btn-outline-secondary btn-sm btn-cancel-edit-category">Отмена</button>' +
            '    </div>' +
            '  </div>' +
            '</div>' +
            '<div class="category-body">' +
            '  <div class="add-purchase-wrap px-3 py-2">' +
            '    <button class="btn btn-sm btn-outline-secondary btn-add-purchase" data-category-id="' + cat.id + '"><i class="bi bi-plus"></i> Добавить товар</button>' +
            '    <div class="new-purchase-form bg-white border rounded p-2 mt-1" style="display:none;">' +
            '      <div class="row g-2">' +
            '        <div class="col-12"><input type="text" class="new-purchase-name form-control form-control-sm" placeholder="Название">' +
            '          <div class="invalid-feedback new-purchase-name-error"></div></div>' +
            '        <div class="col-5"><input type="number" class="new-purchase-quantity form-control form-control-sm" value="1" min="0.01" step="0.01"></div>' +
            '        <div class="col-7"><select class="new-purchase-unit form-select form-select-sm">' + unitsHtml() + '</select></div>' +
            '      </div>' +
            '      <div class="mt-2 d-flex gap-2">' +
            '        <button class="btn btn-primary btn-sm btn-save-new-purchase" data-category-id="' + cat.id + '">Сохранить</button>' +
            '        <button class="btn btn-outline-secondary btn-sm btn-cancel-new-purchase">Отмена</button>' +
            '      </div>' +
            '    </div>' +
            '  </div>' +
            '</div>';
        return div;
    }

    // Expose builders so websocket.js can reuse them for remote events (FR-18)
    window.shopEditUI = {
        buildCategoryBlock: buildCategoryBlock,
        buildPurchaseItem:  buildPurchaseItem,
    };

    function buildPurchaseItem(p) {
        var div = document.createElement('div');
        div.className = 'purchase-item' + (p.is_need_to_buy ? '' : ' is-bought');
        div.dataset.purchaseId = p.id;
        div.innerHTML =
            '<div class="purchase-display d-flex align-items-center w-100 gap-2">' +
            '  <input type="checkbox" class="toggle-checkbox flex-shrink-0" data-purchase-id="' + p.id + '"' + (p.is_need_to_buy ? ' checked' : '') + '>' +
            '  <span class="flex-grow-1 small">' + window.shopUtils.esc(p.name) + ' — ' + window.shopUtils.fmtQty(p.quantity) + ' ' + window.shopUtils.esc(p.unit_abbreviation) + '</span>' +
            '  <button class="btn btn-sm btn-link p-1 btn-edit-purchase" data-purchase-id="' + p.id + '"><i class="bi bi-pencil"></i></button>' +
            '  <button class="btn btn-sm btn-link p-1 text-danger btn-delete-purchase" data-purchase-id="' + p.id + '"><i class="bi bi-trash"></i></button>' +
            '</div>' +
            '<div class="purchase-edit-form w-100 bg-white border-top p-2" style="display:none;">' +
            '  <div class="row g-2">' +
            '    <div class="col-12"><input type="text" class="edit-purchase-name form-control form-control-sm" value="' + window.shopUtils.esc(p.name) + '" placeholder="Название">' +
            '      <div class="invalid-feedback edit-purchase-name-error"></div></div>' +
            '    <div class="col-5"><input type="number" class="edit-purchase-quantity form-control form-control-sm" value="' + p.quantity + '" min="0.01" step="0.01"></div>' +
            '    <div class="col-7"><select class="edit-purchase-unit form-select form-select-sm">' + unitsHtml(p.unit_id) + '</select></div>' +
            '  </div>' +
            '  <div class="mt-2 d-flex gap-2">' +
            '    <button class="btn btn-primary btn-sm btn-save-edit-purchase" data-purchase-id="' + p.id + '">Сохранить</button>' +
            '    <button class="btn btn-outline-secondary btn-sm btn-cancel-edit-purchase">Отмена</button>' +
            '  </div>' +
            '</div>';
        return div;
    }
})();
