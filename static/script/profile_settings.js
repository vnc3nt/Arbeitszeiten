let dialogNormalShowModal = HTMLDialogElement.prototype.showModal;

let dialogCloseOnClick = (e) => {
    // close when clicking outside of the modal
    e.stopPropagation();
    let elem = e.target;
    while (elem.tagName != "DIALOG") {
        elem = elem.parentNode;
    }
    if (elem.offsetTop > e.y || elem.offsetTop + elem.offsetHeight < e.y || elem.offsetLeft - elem.offsetWidth / 2 > e.x || elem.offsetLeft + elem.offsetWidth / 2 < e.x) {
        elem.close();
    }
};

window.addEventListener("keydown", (e) => {
    if (e.key == "Escape") {
        let bg_modal = document.getElementById("modal-background");
        bg_modal.style.display = "none";
    }
}, true)

HTMLDialogElement.prototype.showModal = function () {
    let bg_modal = document.getElementById("modal-background");
    bg_modal.style.display = "block";
    dialogNormalShowModal.apply(this, arguments);
    this.addEventListener("click", dialogCloseOnClick);
};

let dialogNormalModalClose = HTMLDialogElement.prototype.close;
HTMLDialogElement.prototype.close = function () {
    
    let bg_modal = document.querySelector("#modal-background");
    bg_modal.style.display = "none";
    background_modal_event = undefined;
    

    dialogNormalModalClose.apply(this, arguments);
    this.removeEventListener("click", dialogCloseOnClick);
};


window.addEventListener("DOMContentLoaded", (e) => {
    let change_user_name_btn = document.getElementById("changeUsernameBtn");
    let change_username_dialog = document.getElementById("change-user-name-dialog");
    
    change_username_dialog.querySelector("input[type=reset]").addEventListener("click", (e) => {
        change_username_dialog.close();
    })

    change_username_dialog.querySelector("input[type=submit]").addEventListener("click", async (e) => {
        e.preventDefault();
        let res = await fetch("/api/check-existance",
            {
                method: "POST",
                body:JSON.stringify({
                    "type": "username",
                    "value": change_username_dialog.querySelector("input[name=new_username]").value,
                }),
                headers: {
                    "Accept": "application/json, text/plain, */*",
                    "Content-type": "application/json; charset=UTF-8"
                }
            }
        ).then((resp) => resp.json());
        console.log(res);
        if (!res.exists) {
            change_username_dialog.querySelector("form").submit();
        }
        else {
            alert("Benutzername existiert bereits");
        }
    })

    change_user_name_btn.addEventListener("click", (e) => {
        change_username_dialog.querySelector("input[name=new_username]").value = document.querySelector(".username").innerText.trim();
        change_username_dialog.showModal();
    })
})

window.addEventListener("DOMContentLoaded", (e) => {
    let delete_account_btn = document.getElementById("deleteAccountBtn");
    let delete_acc_dialog = document.getElementById("delete-account-dialog");

    delete_acc_dialog.querySelector("input[type=reset]").addEventListener("click", (e) => {
        delete_acc_dialog.close();
    })

    delete_account_btn.addEventListener("click", (e) => {
        delete_acc_dialog.showModal();
        delete_acc_dialog.querySelector("input#password").focus();
    });
});


window.addEventListener("DOMContentLoaded", (e) => {
    let change_password_btn = document.getElementById("changePasswordBtn");
    let change_password_dialog = document.getElementById("change-password-dialog");

    change_password_dialog.querySelector("input[type=reset]").addEventListener("click", (e) => {
        change_password_dialog.close();
    })

    change_password_btn.addEventListener("click", (e) => {
        change_password_dialog.showModal();
        change_password_dialog.querySelector("input").focus();
    });
})

// Touch-Funktionalität für das Profil-Menü
window.addEventListener("DOMContentLoaded", (e) => {
    const profileMenu = document.getElementById('profile-menu');
    const profileButton = document.querySelector('.profile');
    
    if (!profileMenu || !profileButton) return;
    
    let startY = 0;
    let currentY = 0;
    let isDragging = false;
    
    // Touch-Events für das Profil-Menü
    profileMenu.addEventListener('touchstart', function(e) {
        // Prüfen ob das Menü sichtbar ist
        const details = profileButton.querySelector('details');
        if (!details || !details.open) return;
        
        startY = e.touches[0].clientY;
        currentY = startY;
        isDragging = true;
        
        // Animation während des Drags deaktivieren
        profileMenu.style.transition = 'none';
        
        e.preventDefault();
    }, { passive: false });
    
    profileMenu.addEventListener('touchmove', function(e) {
        if (!isDragging) return;
        
        currentY = e.touches[0].clientY;
        const deltaY = currentY - startY;
        
        // Nur nach unten wischen erlauben (positive deltaY)
        if (deltaY > 0) {
            const translateY = Math.min(deltaY, window.innerHeight);
            profileMenu.style.transform = `translateY(${translateY}px)`;
        }
        
        e.preventDefault();
    }, { passive: false });
    
    profileMenu.addEventListener('touchend', function(e) {
        if (!isDragging) return;
        
        isDragging = false;
        const deltaY = currentY - startY;
        const threshold = window.innerHeight * 0.25; // 25% der Bildschirmhöhe
        
        // Animation wieder aktivieren
        profileMenu.style.transition = 'transform 0.3s ease-out';
        
        if (deltaY > threshold) {
            // Menü schließen - nach unten ausblenden
            profileMenu.style.transform = `translateY(100%)`;
            
            // Nach der Animation das Menü verstecken
            setTimeout(() => {
                const details = profileButton.querySelector('details');
                if (details) {
                    details.removeAttribute('open');
                }
                profileMenu.style.transform = '';
                profileMenu.style.transition = '';
            }, 300);
        } else {
            // Menü zurück zur ursprünglichen Position
            profileMenu.style.transform = 'translateY(0)';
            setTimeout(() => {
                profileMenu.style.transition = '';
            }, 300);
        }
        
        e.preventDefault();
    }, { passive: false });
    
    // Überschreibung des Klick-Verhaltens für animiertes Schließen
    const profileDetails = profileButton.querySelector('details');
    const profileSummary = profileButton.querySelector('summary');
    
    if (profileDetails && profileSummary) {
        // Verhindere das Standard-toggle-Verhalten
        profileSummary.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (profileDetails.open) {
                // Menü ist offen - Animation zum Schließen
                profileMenu.classList.add('closing');
                
                // Desktop: kürzere Verzögerung, Mobile: längere für Touch-Animation
                const isDesktop = window.innerWidth >= 766;
                const delay = isDesktop ? 150 : 300;
                
                // Nach der Animation das details-Element schließen
                setTimeout(() => {
                    profileDetails.removeAttribute('open');
                    profileMenu.classList.remove('closing');
                }, delay);
            } else {
                // Menü ist geschlossen - normal öffnen
                profileDetails.setAttribute('open', '');
                profileMenu.classList.remove('closing');
                setTimeout(() => {
                    profileMenu.style.transform = '';
                    profileMenu.style.transition = '';
                }, 50);
            }
        });
        
        // Fallback für toggle-Event (für andere Schließ-Methoden)
        profileDetails.addEventListener('toggle', function() {
            if (this.open) {
                // Menü wird geöffnet - sicherstellen dass closing-Klasse entfernt ist
                profileMenu.classList.remove('closing');
                setTimeout(() => {
                    profileMenu.style.transform = '';
                    profileMenu.style.transition = '';
                }, 50);
            }
        });
    }
})
