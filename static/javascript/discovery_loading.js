
/* Loading feedback for the server-rendered Resource Discovery search form. */
(() => {
    'use strict';

    const overlay = document.getElementById('discovery-loading');
    const form = document.getElementById('search-form');
    if (!overlay || !form) return;

    let submitting = false;

    function resetLoading() {
        overlay.hidden = true;
        submitting = false;
    }

    // The sidebar Apply button uses form="search-form", so it also triggers
    // this submit event even though the button is outside the form element.
    form.addEventListener('submit', (event) => {
        if (event.defaultPrevented || !form.checkValidity()) return;
        if (submitting) {
            event.preventDefault();
            return;
        }
        submitting = true;
        overlay.hidden = false;

        // If another submit handler cancels navigation, restore the page.
        queueMicrotask(() => {
            if (event.defaultPrevented) resetLoading();
        });
    });

    // Restore the page after browser Back/Forward cache navigation.
    window.addEventListener('pageshow', resetLoading);
})();
