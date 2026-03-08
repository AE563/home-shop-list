'use strict';
/**
 * Tests for static/js/websocket.js
 * Covers: WS URL, buildViewPurchaseItem, buildViewCategoryBlock,
 *         handleEvent for purchase/category events, reconnect, offline banner.
 */

const fs = require('fs');
const path = require('path');

const WS_CODE = fs.readFileSync(
  path.join(__dirname, '../../static/js/websocket.js'),
  'utf8'
);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Load websocket.js into the JSDOM context with mocked globals.
 * Returns the mock WebSocket instance and registered event listeners.
 */
function loadWS({ protocol = 'http:', host = 'localhost', extraDom = '' } = {}) {
  document.body.innerHTML = `
    <div id="offline-banner" style="display:none;"></div>
    ${extraDom}
  `;

  const listeners = {};
  const mockSocket = {
    addEventListener: jest.fn((event, handler) => {
      listeners[event] = handler;
    }),
    close: jest.fn(),
    send: jest.fn(),
  };

  const MockWebSocket = jest.fn(() => mockSocket);

  const fn = new Function(
    'window', 'document', 'location', 'WebSocket', 'setTimeout', 'clearTimeout', 'console',
    WS_CODE
  );
  fn(
    window, document,
    { protocol, host },
    MockWebSocket,
    jest.fn(),  // setTimeout (prevents real reconnect timers)
    jest.fn(),  // clearTimeout
    console
  );

  return { MockWebSocket, mockSocket, listeners };
}

// ---------------------------------------------------------------------------
// WS URL construction
// ---------------------------------------------------------------------------

describe('WebSocket URL', () => {
  test('uses ws:// for http protocol', () => {
    const { MockWebSocket } = loadWS({ protocol: 'http:', host: 'example.com' });
    expect(MockWebSocket).toHaveBeenCalledWith('ws://example.com/ws/shop/');
  });

  test('uses wss:// for https protocol', () => {
    const { MockWebSocket } = loadWS({ protocol: 'https:', host: 'example.com' });
    expect(MockWebSocket).toHaveBeenCalledWith('wss://example.com/ws/shop/');
  });
});

// ---------------------------------------------------------------------------
// Offline banner
// ---------------------------------------------------------------------------

describe('offline banner', () => {
  test('banner is shown on disconnect', () => {
    const { listeners } = loadWS();
    const banner = document.getElementById('offline-banner');
    listeners['close']();
    expect(banner.style.display).toBe('block');
  });

  test('banner is hidden on reconnect (open)', () => {
    const { listeners } = loadWS();
    const banner = document.getElementById('offline-banner');
    banner.style.display = 'block';
    listeners['open']();
    expect(banner.style.display).toBe('none');
  });

  test('banner text is set on disconnect', () => {
    const { listeners } = loadWS();
    const banner = document.getElementById('offline-banner');
    listeners['close']();
    expect(banner.textContent).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Reconnect on close (FR-19)
// ---------------------------------------------------------------------------

describe('auto-reconnect', () => {
  test('onclose schedules reconnect via setTimeout', () => {
    const mockSetTimeout = jest.fn();

    const fn = new Function(
      'window', 'document', 'location', 'WebSocket', 'setTimeout', 'clearTimeout', 'console',
      WS_CODE
    );
    document.body.innerHTML = '<div id="offline-banner"></div>';
    const mockSocket = {
      addEventListener: jest.fn((event, handler) => { listeners2[event] = handler; }),
      close: jest.fn(),
    };
    const listeners2 = {};
    fn(
      window, document,
      { protocol: 'http:', host: 'localhost' },
      jest.fn(() => mockSocket),
      mockSetTimeout,
      jest.fn(),
      console
    );

    listeners2['close']();
    expect(mockSetTimeout).toHaveBeenCalled();
    const [, delay] = mockSetTimeout.mock.calls[0];
    expect(delay).toBe(3000);
  });
});

// ---------------------------------------------------------------------------
// purchase.created on view page
// ---------------------------------------------------------------------------

describe('purchase.created event on view page', () => {
  function sendMessage(listeners, payload) {
    listeners['message']({ data: JSON.stringify(payload) });
  }

  test('inserts purchase into #shop-view when is_need_to_buy=true', () => {
    const { listeners } = loadWS({
      extraDom: '<div id="shop-view"></div>',
    });

    sendMessage(listeners, {
      type: 'purchase.created',
      purchase: {
        id: 1,
        name: 'Молоко',
        is_need_to_buy: true,
        quantity: '2',
        unit_abbreviation: 'шт.',
        category_id: 10,
        category_name: 'Молочное',
        category_order: 1,
      },
    });

    expect(document.querySelector('#shop-view [data-purchase-id="1"]')).not.toBeNull();
  });

  test('creates category block if it does not exist', () => {
    const { listeners } = loadWS({
      extraDom: '<div id="shop-view"></div>',
    });

    sendMessage(listeners, {
      type: 'purchase.created',
      purchase: {
        id: 2,
        name: 'Сыр',
        is_need_to_buy: true,
        quantity: '0.3',
        unit_abbreviation: 'кг',
        category_id: 20,
        category_name: 'Молочное',
        category_order: 1,
      },
    });

    expect(document.querySelector('#shop-view .category-block[data-category-id="20"]')).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// buildViewPurchaseItem — tested via purchase.created DOM output
// ---------------------------------------------------------------------------

describe('buildViewPurchaseItem', () => {
  function insertPurchase(listeners, p) {
    listeners['message']({
      data: JSON.stringify({ type: 'purchase.created', purchase: p }),
    });
  }

  test('rendered item has data-purchase-id', () => {
    const { listeners } = loadWS({ extraDom: '<div id="shop-view"></div>' });
    insertPurchase(listeners, {
      id: 5,
      name: 'Кефир',
      is_need_to_buy: true,
      quantity: '1',
      unit_abbreviation: 'л',
      category_id: 3,
      category_name: 'Молочное',
      category_order: 1,
    });

    const item = document.querySelector('[data-purchase-id="5"]');
    expect(item).not.toBeNull();
  });

  test('rendered item has a checked checkbox', () => {
    const { listeners } = loadWS({ extraDom: '<div id="shop-view"></div>' });
    insertPurchase(listeners, {
      id: 6,
      name: 'Масло',
      is_need_to_buy: true,
      quantity: '200',
      unit_abbreviation: 'г',
      category_id: 3,
      category_name: 'Молочное',
      category_order: 1,
    });

    const cb = document.querySelector('[data-purchase-id="6"] .toggle-checkbox');
    expect(cb).not.toBeNull();
    expect(cb.checked).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// buildViewCategoryBlock — tested via purchase.created DOM output
// ---------------------------------------------------------------------------

describe('buildViewCategoryBlock', () => {
  test('rendered block contains category name', () => {
    const { listeners } = loadWS({ extraDom: '<div id="shop-view"></div>' });

    listeners['message']({
      data: JSON.stringify({
        type: 'purchase.created',
        purchase: {
          id: 9,
          name: 'Хлеб',
          is_need_to_buy: true,
          quantity: '1',
          unit_abbreviation: 'шт.',
          category_id: 50,
          category_name: 'Выпечка',
          category_order: 2,
        },
      }),
    });

    const block = document.querySelector('.category-block[data-category-id="50"]');
    expect(block).not.toBeNull();
    expect(block.innerHTML).toContain('Выпечка');
  });
});

// ---------------------------------------------------------------------------
// purchase.updated event
// ---------------------------------------------------------------------------

describe('purchase.updated event on view page', () => {
  function setup() {
    const { listeners } = loadWS({
      extraDom: `
        <div id="shop-view">
          <div class="category-block" data-category-id="1">
            <div class="category-body">
              <div class="purchase-item" data-purchase-id="10">
                <span></span>
              </div>
            </div>
          </div>
        </div>
      `,
    });
    return listeners;
  }

  test('removes item from view when is_need_to_buy becomes false', () => {
    const listeners = setup();
    listeners['message']({
      data: JSON.stringify({
        type: 'purchase.updated',
        purchase: {
          id: 10,
          name: 'Молоко',
          is_need_to_buy: false,
          quantity: '1',
          unit_abbreviation: 'шт.',
          category_id: 1,
          category_name: 'Молочное',
          category_order: 1,
        },
      }),
    });

    expect(document.querySelector('#shop-view [data-purchase-id="10"]')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// purchase.deleted event
// ---------------------------------------------------------------------------

describe('purchase.deleted event on view page', () => {
  test('removes item from #shop-view', () => {
    const { listeners } = loadWS({
      extraDom: `
        <div id="shop-view">
          <div class="category-block" data-category-id="1">
            <div class="category-body">
              <div class="purchase-item" data-purchase-id="11"></div>
            </div>
          </div>
        </div>
      `,
    });

    listeners['message']({
      data: JSON.stringify({ type: 'purchase.deleted', purchase_id: 11 }),
    });

    expect(document.querySelector('#shop-view [data-purchase-id="11"]')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// category.deleted event
// ---------------------------------------------------------------------------

describe('category.deleted event', () => {
  test('removes category block from DOM', () => {
    const { listeners } = loadWS({
      extraDom: `
        <div id="shop-view">
          <div class="category-block" data-category-id="7"></div>
        </div>
      `,
    });

    listeners['message']({
      data: JSON.stringify({ type: 'category.deleted', category_id: 7 }),
    });

    expect(document.querySelector('.category-block[data-category-id="7"]')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// category.updated event on view page
// ---------------------------------------------------------------------------

describe('category.updated event on view page', () => {
  test('updates category name in #shop-view', () => {
    const { listeners } = loadWS({
      extraDom: `
        <div id="shop-view">
          <div class="category-block" data-category-id="3">
            <div class="category-header">
              <span class="fw-semibold">Старое название</span>
            </div>
          </div>
        </div>
      `,
    });

    listeners['message']({
      data: JSON.stringify({
        type: 'category.updated',
        category: { id: 3, name: 'Новое название', order: 1 },
      }),
    });

    const nameEl = document.querySelector('.category-block[data-category-id="3"] .fw-semibold');
    expect(nameEl.textContent).toBe('Новое название');
  });
});

// ---------------------------------------------------------------------------
// Invalid JSON in message — should not throw
// ---------------------------------------------------------------------------

describe('invalid WebSocket message', () => {
  test('invalid JSON is silently ignored', () => {
    const { listeners } = loadWS();
    expect(() => {
      listeners['message']({ data: 'not valid json{{{{' });
    }).not.toThrow();
  });
});
