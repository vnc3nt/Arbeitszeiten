document.addEventListener('DOMContentLoaded', function() {
    const backLink = document.getElementById('backLink') || document.querySelector('.backbutton');
    if (!backLink) {
        return; // Kein Fehler mehr auf Seiten ohne Zurück-Button!
    }

    backLink.addEventListener('click', function(e) {
        if (document.referrer) {
            try {
                const referrer = new URL(document.referrer);
                if (referrer.hostname === window.location.hostname) {
                    e.preventDefault();
                    window.history.back();
                }
            } catch (err) {
                // Fallback auf normalen href-Link
            }
        }
    });
});