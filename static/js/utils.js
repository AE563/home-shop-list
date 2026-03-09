'use strict';
window.shopUtils = {
    esc: function (s) {
        return String(s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    },
    fmtQty: function (qty) {
        var n = parseFloat(qty);
        if (isNaN(n)) return String(qty);
        return n === Math.floor(n) ? String(n) : n.toFixed(2).replace(/0+$/, '').replace(/\.$/, '');
    },
};
