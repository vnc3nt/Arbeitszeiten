document.addEventListener('DOMContentLoaded', function() {
    var backLink = document.getElementById('backLink');
    
    backLink.addEventListener('click', function(e) {
        e.preventDefault(); // Verhindert das Standard-Verhalten des Links
        
        if(document.referrer) {
            // Überprüfen, ob die vorherige Seite zur gleichen Domain gehört
            var referrer = new URL(document.referrer);
            if(referrer.hostname === window.location.hostname) {
                window.history.back(); // Geht zur vorherigen Seite zurück
            } else {
                window.location.href = '/'; // Geht zur Homepage, wenn die vorherige Seite von einer anderen Domain war
            }
        } else {
            window.location.href = '/'; // Geht zur Homepage, wenn es keine vorherige Seite gibt
        }
    });
});