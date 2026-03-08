/**
 * websocket.js — WebSocket connection and real-time event handling (FR-18, FR-19)
 *
 * Message format (PRD 8.5):
 *   { type: "purchase.updated",  purchase: {...} }
 *   { type: "purchase.created",  purchase: {...} }
 *   { type: "purchase.deleted",  purchase_id: 42, category_id: 5 }
 *   { type: "category.created",  category: { id, name, order } }
 *   { type: "category.updated",  category: { id, name, order } }
 *   { type: "category.deleted",  category_id: 7 }
 */

'use strict';

(function () {
    var WS_URL = (location.protocol === 'https:' ? 'wss' : 'ws') + '://' + location.host + '/ws/shop/';
    var RECONNECT_DELAY_MS = 3000;
    var banner = document.getElementById('offline-banner');

    var socket = null;
    var reconnectTimer = null;

    // -----------------------------------------------------------------------
    // Connection management (FR-19: auto-reconnect)
    // -----------------------------------------------------------------------
    function connect() {
        socket = new WebSocket(WS_URL);

        socket.addEventListener('open', function () {
            if (banner) banner.style.display = 'none';
            clearTimeout(reconnectTimer);
        });

        socket.addEventListener('close', function () {
            showOfflineBanner();
            reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
        });

        socket.addEventListener('error', function () {
            socket.close();
        });

        socket.addEventListener('message', function (event) {
            var data;
            try {
                data = JSON.parse(event.data);
            } catch (e) {
                console.error('WS: invalid JSON', event.data);
                return;
            }
            handleEvent(data);
        });
    }

    function showOfflineBanner() {
        if (banner) {
            banner.textContent = 'Соединение потеряно, переподключение...';
            banner.style.display = 'block';
        }
    }

    // -----------------------------------------------------------------------
    // Event dispatcher
    // -----------------------------------------------------------------------
    function handleEvent(data) {
        if (!data || !data.type) return;
        var handlers = {
            'purchase.created': onPurchaseCreated,
            'purchase.updated': onPurchaseUpdated,
            'purchase.deleted': onPurchaseDeleted,
            'category.created': onCategoryCreated,
            'category.updated': onCategoryUpdated,
            'category.deleted': onCategoryDeleted,
        };
        var fn = handlers[data.type];
        if (fn) fn(data);
    }

    // -----------------------------------------------------------------------
    // Helpers (duplicated from ui.js scope — same logic, different scope)
    // -----------------------------------------------------------------------
    var isViewPage = !!document.getElementById('shop-view');
    var isEditPage = !!document.getElementById('shop-edit');

    function esc(s) {
        return String(s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function fmtQty(qty) {
        var n = parseFloat(qty);
        if (isNaN(n)) return String(qty);
        return n === Math.floor(n) ? String(n) : n.toFixed(2).replace(/0+$/, '').replace(/\.$/, '');
    }

    // -----------------------------------------------------------------------
    // Purchase handlers
    // -----------------------------------------------------------------------

    function onPurchaseCreated(data) {
        var p = data.purchase;
        if (!p) return;

        if (isViewPage && p.is_need_to_buy) {
            insertPurchaseIntoView(p);
        }
        if (isEditPage) {
            // Avoid duplicate if own action already added it
            if (!document.querySelector('#shop-edit .purchase-item[data-purchase-id="' + p.id + '"]')) {
                insertPurchaseIntoEdit(p);
            }
        }
    }

    function onPurchaseUpdated(data) {
        var p = data.purchase;
        if (!p) return;

        if (isViewPage) {
            var viewItem = document.querySelector('#shop-view [data-purchase-id="' + p.id + '"]');
            if (!p.is_need_to_buy) {
                if (viewItem) removeViewItem(p.id);
            } else {
                if (viewItem) {
                    var span = viewItem.querySelector('span');
                    if (span) span.innerHTML = esc(p.name) + '<small class="text-muted ms-1">— ' + esc(fmtQty(p.quantity)) + ' ' + esc(p.unit_abbreviation) + '</small>';
                } else {
                    insertPurchaseIntoView(p);
                }
            }
        }

        if (isEditPage) {
            var item = document.querySelector('#shop-edit .purchase-item[data-purchase-id="' + p.id + '"]');
            if (!item) return;
            // Update display text
            var span = item.querySelector('.purchase-display .flex-grow-1');
            if (span) span.textContent = p.name + ' — ' + fmtQty(p.quantity) + ' ' + p.unit_abbreviation;
            // Update checkbox + dim
            var cb = item.querySelector('.toggle-checkbox');
            if (cb) cb.checked = p.is_need_to_buy;
            item.classList.toggle('is-bought', !p.is_need_to_buy);
            // Sync edit form fields
            var nameInput = item.querySelector('.edit-purchase-name');
            if (nameInput) nameInput.value = p.name;
            var qtyInput = item.querySelector('.edit-purchase-quantity');
            if (qtyInput) qtyInput.value = p.quantity;
            var unitSel = item.querySelector('.edit-purchase-unit');
            if (unitSel) {
                Array.from(unitSel.options).forEach(function (opt) {
                    opt.selected = String(opt.value) === String(p.unit_id);
                });
            }
        }
    }

    function onPurchaseDeleted(data) {
        var pk = data.purchase_id;
        if (!pk) return;

        if (isViewPage) removeViewItem(pk);

        if (isEditPage) {
            var item = document.querySelector('#shop-edit .purchase-item[data-purchase-id="' + pk + '"]');
            if (!item) return;
            var block = item.closest('.category-block');
            item.remove();
            if (block) {
                var delBtn = block.querySelector('.btn-delete-category');
                if (delBtn) {
                    var cnt = parseInt(delBtn.dataset.purchaseCount) || 0;
                    delBtn.dataset.purchaseCount = Math.max(0, cnt - 1);
                }
            }
        }
    }

    // -----------------------------------------------------------------------
    // Category handlers
    // -----------------------------------------------------------------------

    function onCategoryCreated(data) {
        var cat = data.category;
        if (!cat) return;
        // View page: skip — empty category has no purchases to show
        if (isEditPage && window.shopEditUI) {
            if (document.querySelector('#shop-edit .category-block[data-category-id="' + cat.id + '"]')) return;
            var noMsg = document.getElementById('no-categories-msg');
            if (noMsg) noMsg.remove();
            document.getElementById('shop-edit').appendChild(window.shopEditUI.buildCategoryBlock(cat));
        }
    }

    function onCategoryUpdated(data) {
        var cat = data.category;
        if (!cat) return;

        if (isViewPage) {
            var block = document.querySelector('#shop-view .category-block[data-category-id="' + cat.id + '"]');
            if (block) {
                var nameEl = block.querySelector('.fw-semibold');
                if (nameEl) nameEl.textContent = cat.name;
            }
        }

        if (isEditPage) {
            var block = document.querySelector('#shop-edit .category-block[data-category-id="' + cat.id + '"]');
            if (!block) return;
            var nameDisplay = block.querySelector('.category-name-display');
            if (nameDisplay) nameDisplay.textContent = cat.name;
            var pb = block.querySelector('.priority-badge');
            if (pb) pb.textContent = 'приоритет: ' + cat.order;
            var nameInput = block.querySelector('.edit-cat-name');
            if (nameInput) nameInput.value = cat.name;
            var orderInput = block.querySelector('.edit-cat-order');
            if (orderInput) orderInput.value = cat.order;
            var delBtn = block.querySelector('.btn-delete-category');
            if (delBtn) delBtn.dataset.categoryName = cat.name;
        }
    }

    function onCategoryDeleted(data) {
        var pk = data.category_id;
        if (!pk) return;

        var block = document.querySelector('.category-block[data-category-id="' + pk + '"]');
        if (block) block.remove();

        if (isViewPage && !document.querySelector('#shop-view .category-block')) {
            showEmptyState('#shop-view', 'empty-state', 'Всё куплено! Список покупок пуст.');
        }
        if (isEditPage && !document.querySelector('#shop-edit .category-block')) {
            showEmptyState('#shop-edit', 'no-categories-msg', 'Нет категорий. Добавьте первую!');
        }
    }

    // -----------------------------------------------------------------------
    // View-page DOM helpers
    // -----------------------------------------------------------------------

    function buildViewPurchaseItem(p) {
        var div = document.createElement('div');
        div.className = 'purchase-item';
        div.dataset.purchaseId = p.id;
        var cid = 'vp' + p.id;
        div.innerHTML =
            '<input type="checkbox" class="toggle-checkbox" id="' + cid + '" data-purchase-id="' + p.id + '" checked>' +
            '<label for="' + cid + '" class="flex-grow-1 mb-0">' +
            '<span>' + esc(p.name) + '<small class="text-muted ms-1">— ' + esc(fmtQty(p.quantity)) + ' ' + esc(p.unit_abbreviation) + '</small></span>' +
            '</label>';
        return div;
    }

    function buildViewCategoryBlock(p) {
        var div = document.createElement('div');
        div.className = 'category-block';
        div.dataset.categoryId = p.category_id;
        div.innerHTML =
            '<div class="category-header">' +
            '  <span class="fw-semibold">' + esc(p.category_name) + '</span>' +
            '  <i class="bi bi-chevron-down collapse-icon"></i>' +
            '</div>' +
            '<div class="category-body"></div>';
        return div;
    }

    function insertPurchaseIntoView(p) {
        var view = document.getElementById('shop-view');
        if (!view) return;
        var empty = document.getElementById('empty-state');
        if (empty) empty.remove();

        var block = view.querySelector('.category-block[data-category-id="' + p.category_id + '"]');
        if (!block) {
            block = buildViewCategoryBlock(p);
            view.appendChild(block);
        }
        if (block.querySelector('[data-purchase-id="' + p.id + '"]')) return;
        var body = block.querySelector('.category-body');
        if (body) body.appendChild(buildViewPurchaseItem(p));
    }

    function removeViewItem(pk) {
        var item = document.querySelector('#shop-view [data-purchase-id="' + pk + '"]');
        if (!item) return;
        var block = item.closest('.category-block');
        item.remove();
        if (block && !block.querySelector('.purchase-item')) block.remove();
        var view = document.getElementById('shop-view');
        if (view && !view.querySelector('.category-block')) {
            showEmptyState('#shop-view', 'empty-state', 'Всё куплено! Список покупок пуст.');
        }
    }

    // -----------------------------------------------------------------------
    // Edit-page helper (delegates to shopEditUI builders in ui.js)
    // -----------------------------------------------------------------------

    function insertPurchaseIntoEdit(p) {
        if (!window.shopEditUI) return;
        var block = document.querySelector('#shop-edit .category-block[data-category-id="' + p.category_id + '"]');
        if (!block) return;
        var wrap = block.querySelector('.add-purchase-wrap');
        var item = window.shopEditUI.buildPurchaseItem(p);
        block.querySelector('.category-body').insertBefore(item, wrap || null);
        var delBtn = block.querySelector('.btn-delete-category');
        if (delBtn) delBtn.dataset.purchaseCount = parseInt(delBtn.dataset.purchaseCount || 0) + 1;
    }

    // -----------------------------------------------------------------------
    // Generic empty-state helper
    // -----------------------------------------------------------------------
    function showEmptyState(containerSelector, msgId, text) {
        var container = document.querySelector(containerSelector);
        if (!container || document.getElementById(msgId)) return;
        var p = document.createElement('p');
        p.id = msgId;
        p.className = 'text-muted text-center mt-5';
        p.textContent = text;
        container.appendChild(p);
    }

    connect();
})();
