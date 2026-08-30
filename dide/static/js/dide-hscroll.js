/*
 * Οριζόντια κύλιση για τους πίνακες των οδηγών εισαγωγής/ενημέρωσης.
 *
 * Ο πίνακας κυλάει μέσα στο δικό του πλαίσιο, ώστε η σελίδα να μη
 * χρειάζεται ποτέ οριζόντια κύλιση. Με σκέτο CSS όμως (max-height: 70vh)
 * το κάτω άκρο του πλαισίου — εκεί που βρίσκεται η οριζόντια μπάρα —
 * έπεφτε 115 έως 175 pixel κάτω από το ορατό παράθυρο: για να κυλήσει
 * κανείς δεξιά έπρεπε πρώτα να κατεβάσει τη σελίδα και να βρει τη μπάρα.
 *
 * Εδώ το ύψος υπολογίζεται από τη θέση του πλαισίου, ώστε η μπάρα να
 * είναι πάντα μέσα στο παράθυρο, μαζί με το κουμπί υποβολής που
 * ακολουθεί. Χωρίς JavaScript μένει το 70vh του CSS.
 */
(function () {
    'use strict';

    var MIN_HEIGHT = 220;   // πιο κοντό δεν έχει νόημα
    var GAP = 24;           // αέρας κάτω από το πλαίσιο

    function reserved(box) {
        // Χώρος για τη μπάρα υποβολής που ακολουθεί τον πίνακα. Μετά το
        // τύλιγμα, ο επόμενος αδελφός του πλαισίου είναι κουμπί κύλισης,
        // οπότε ψάχνουμε από το περίβλημα και μετά.
        var node = box.parentNode
            && box.parentNode.classList.contains('dide-hscroll-wrap')
            ? box.parentNode : box;
        var next = node.nextElementSibling;
        while (next) {
            if (next.classList.contains('submit-row')) {
                return next.offsetHeight + GAP;
            }
            next = next.nextElementSibling;
        }
        return GAP;
    }

    function fit(box) {
        var top = box.getBoundingClientRect().top;
        // Αν η σελίδα έχει κυλήσει και το πλαίσιο ξεκινά πάνω από το
        // παράθυρο, μετράει μόνο ό,τι φαίνεται.
        var available = window.innerHeight - Math.max(top, 0) - reserved(box);
        box.style.maxHeight = Math.max(MIN_HEIGHT, Math.round(available)) + 'px';
    }

    function shade(box) {
        var remaining = box.scrollWidth - box.clientWidth - box.scrollLeft;
        var wrap = box.parentNode;
        box.classList.toggle('has-more', remaining > 2);
        box.classList.toggle('has-less', box.scrollLeft > 2);
        if (wrap && wrap.classList.contains('dide-hscroll-wrap')) {
            wrap.classList.toggle('can-right', remaining > 2);
            wrap.classList.toggle('can-left', box.scrollLeft > 2);
        }
    }

    /*
     * Κουμπιά κύλισης δεξιά/αριστερά. Η μπάρα του φυλλομετρητή δεν αρκεί:
     * σε macOS κρύβεται όσο δεν κυλάει κανείς, και σε επικαλυπτόμενες
     * μπάρες μόλις διακρίνεται. Τα κουμπιά φαίνονται πάντα, δείχνουν ότι
     * ο πίνακας συνεχίζεται, και λειτουργούν και με το πληκτρολόγιο.
     */
    function addButtons(box) {
        var wrap = document.createElement('div');
        wrap.className = 'dide-hscroll-wrap';
        box.parentNode.insertBefore(wrap, box);
        wrap.appendChild(box);

        [['left', '\u2039', 'Κύλιση αριστερά'],
         ['right', '\u203a', 'Κύλιση δεξιά']].forEach(function (spec) {
            var btn = document.createElement('button');
            // Μέσα σε <form>: χωρίς type="button" θα υπέβαλλε τη φόρμα.
            btn.type = 'button';
            btn.className = 'dide-pan dide-pan-' + spec[0];
            btn.innerHTML = spec[1];
            btn.setAttribute('aria-label', spec[2]);
            btn.title = spec[2];
            btn.addEventListener('click', function () {
                var step = Math.max(120, Math.round(box.clientWidth * 0.8));
                box.scrollLeft += (spec[0] === 'left' ? -step : step);
            });
            wrap.appendChild(btn);
        });
    }

    function init() {
        var boxes = Array.prototype.slice.call(
            document.querySelectorAll('.dide-hscroll:not(.dide-report)'));
        if (!boxes.length) {
            return;
        }

        boxes.forEach(function (box) {
            // Εστιάσιμο, ώστε να κυλάει και με τα βέλη του πληκτρολογίου.
            if (!box.hasAttribute('tabindex')) {
                box.setAttribute('tabindex', '0');
            }
            addButtons(box);
            fit(box);
            shade(box);
            box.addEventListener('scroll', function () { shade(box); });
        });

        var pending = null;
        function refresh() {
            boxes.forEach(function (box) { fit(box); shade(box); });
        }
        window.addEventListener('resize', function () {
            window.clearTimeout(pending);
            pending = window.setTimeout(refresh, 100);
        });
        // Η θέση του πλαισίου αλλάζει καθώς κυλάει η σελίδα.
        window.addEventListener('scroll', function () {
            window.clearTimeout(pending);
            pending = window.setTimeout(refresh, 100);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
}());
