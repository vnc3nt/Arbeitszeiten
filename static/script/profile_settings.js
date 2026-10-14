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
    if (!change_user_name_btn || !change_username_dialog) return;
    
    change_username_dialog.querySelector("input[type=reset]").addEventListener("click", (e) => {
        change_username_dialog.close();
    })

    change_username_dialog.querySelector("form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const form = change_username_dialog.querySelector("form");
        const newUsername = form.querySelector("input[name=new_username]").value.trim();
        const currentUsername = document.querySelector(".username").innerText.trim();
        if (newUsername === currentUsername) {
            form.submit();
            return;
        }
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            const res = await fetch("/api/check-existence", {
                method: "POST",
                body: JSON.stringify({"type": "username", "value": newUsername}),
                headers: {
                    "Accept": "application/json, text/plain, */*",
                    "Content-type": "application/json; charset=UTF-8",
                    "X-CSRFToken": csrfToken || ""
                }
            }).then((resp) => resp.json());
            if (!res.exists) {
                form.submit();
            } else {
                alert("Benutzername existiert bereits");
            }
        } catch (error) {
            alert("Benutzername konnte nicht geprüft werden");
        }
    })

    change_user_name_btn.addEventListener("click", (e) => {
        change_username_dialog.querySelector("input[name=new_username]").value = document.querySelector(".username").innerText.trim();
        change_username_dialog.showModal();
    })
})

window.addEventListener("DOMContentLoaded", () => {
    const manageProfilesBtn = document.getElementById("manageProfilesBtn");
    const manageProfilesDialog = document.getElementById("manage-profiles-dialog");
    if (manageProfilesBtn && manageProfilesDialog) {
        manageProfilesBtn.addEventListener("click", () => manageProfilesDialog.showModal());
    }
});

window.addEventListener("DOMContentLoaded", (e) => {
    let delete_account_btn = document.getElementById("deleteAccountBtn");
    let delete_acc_dialog = document.getElementById("delete-account-dialog");
    if (!delete_account_btn || !delete_acc_dialog) return;

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
    if (!change_password_btn || !change_password_dialog) return;

    change_password_dialog.querySelector("input[type=reset]").addEventListener("click", (e) => {
        change_password_dialog.close();
    })

    change_password_btn.addEventListener("click", (e) => {
        change_password_dialog.showModal();
        change_password_dialog.querySelector("input").focus();
    });
})

window.addEventListener("DOMContentLoaded", (e) => {
    const changeProfilePicBtn = document.getElementById("changeProfilePic");
    const changeProfilePicDialog = document.getElementById("change-profile-picture-dialog");

    if (!changeProfilePicBtn || !changeProfilePicDialog) return;

    const fileInput = changeProfilePicDialog.querySelector("#profile-image-input");
    const preview = changeProfilePicDialog.querySelector("#profile-image-preview");
    const cropper = changeProfilePicDialog.querySelector("#profile-image-cropper");
    const canvas = changeProfilePicDialog.querySelector("#profile-image-canvas");
    const zoomInput = changeProfilePicDialog.querySelector("#profile-image-zoom");
    const cropForm = changeProfilePicDialog.querySelector("form");
    const context = canvas.getContext("2d");
    const cropImage = new Image();
    let imageScale = 1;
    let imageOffsetX = 0;
    let imageOffsetY = 0;
    let dragStart = null;
    const defaultPreviewSrc = document.querySelector(".profile-pic")?.src;

    changeProfilePicDialog.querySelector("input[type=reset]").addEventListener("click", () => {
        changeProfilePicDialog.close();
        fileInput.value = "";
        cropper.hidden = true;
        cropImage.src = "";
        if (defaultPreviewSrc) {
            preview.src = defaultPreviewSrc;
        }
    });

    const drawCrop = () => {
        if (!cropImage.naturalWidth) return;
        const baseScale = Math.max(canvas.width / cropImage.naturalWidth, canvas.height / cropImage.naturalHeight);
        const scale = baseScale * imageScale;
        const width = cropImage.naturalWidth * scale;
        const height = cropImage.naturalHeight * scale;
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(cropImage, imageOffsetX, imageOffsetY, width, height);
    };

    fileInput.addEventListener("change", () => {
        const file = fileInput.files && fileInput.files[0];
        if (!file) {
            cropper.hidden = true;
            if (defaultPreviewSrc) {
                preview.src = defaultPreviewSrc;
            }
            return;
        }

        const reader = new FileReader();
        reader.onload = (event) => {
            cropImage.onload = () => {
                imageScale = 1;
                const baseScale = Math.max(canvas.width / cropImage.naturalWidth, canvas.height / cropImage.naturalHeight);
                imageOffsetX = (canvas.width - cropImage.naturalWidth * baseScale) / 2;
                imageOffsetY = (canvas.height - cropImage.naturalHeight * baseScale) / 2;
                zoomInput.value = "1";
                cropper.hidden = false;
                drawCrop();
            };
            cropImage.src = event.target.result;
        };
        reader.readAsDataURL(file);
    });

    zoomInput.addEventListener("input", () => {
        imageScale = Number(zoomInput.value);
        drawCrop();
    });

    canvas.addEventListener("pointerdown", (event) => {
        if (!cropImage.naturalWidth) return;
        canvas.setPointerCapture(event.pointerId);
        dragStart = {x: event.clientX, y: event.clientY};
    });

    canvas.addEventListener("pointermove", (event) => {
        if (!dragStart) return;
        const scaleX = canvas.width / canvas.getBoundingClientRect().width;
        const scaleY = canvas.height / canvas.getBoundingClientRect().height;
        imageOffsetX += (event.clientX - dragStart.x) * scaleX;
        imageOffsetY += (event.clientY - dragStart.y) * scaleY;
        dragStart = {x: event.clientX, y: event.clientY};
        drawCrop();
    });

    canvas.addEventListener("pointerup", () => {
        dragStart = null;
    });
    canvas.addEventListener("pointercancel", () => {
        dragStart = null;
    });

    cropForm.addEventListener("submit", (event) => {
        if (!cropImage.naturalWidth) return;
        event.preventDefault();
        canvas.toBlob((blob) => {
            if (!blob) {
                alert("Das Bild konnte nicht zugeschnitten werden");
                return;
            }
            const croppedFile = new File([blob], "profile.png", {type: "image/png"});
            const transfer = new DataTransfer();
            transfer.items.add(croppedFile);
            fileInput.files = transfer.files;
            cropForm.submit();
        }, "image/png");
    });

    changeProfilePicBtn.addEventListener("click", () => {
        fileInput.value = "";
        cropper.hidden = true;
        cropImage.src = "";
        if (defaultPreviewSrc) {
            preview.src = defaultPreviewSrc;
        }
        changeProfilePicDialog.showModal();
        fileInput.focus();
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
        
        // Wenn auf einen Link oder Button geklickt wurde, nicht verhindern
        const target = e.target;
        const isInteractive = target.closest('a, button, [role="button"]');
        if (isInteractive) {
            isDragging = false;
            return;
        }
        
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
        
        // Nur bei signifikanter Bewegung als Drag behandeln (>10px)
        if (Math.abs(deltaY) > 10) {
            // Nur nach unten wischen erlauben (positive deltaY)
            if (deltaY > 0) {
                const translateY = Math.min(deltaY, window.innerHeight);
                profileMenu.style.transform = `translateY(${translateY}px)`;
            }
            e.preventDefault();
        }
    }, { passive: false });
    
    profileMenu.addEventListener('touchend', function(e) {
        if (!isDragging) return;
        
        isDragging = false;
        const deltaY = currentY - startY;
        const threshold = window.innerHeight * 0.25; // 25% der Bildschirmhöhe
        
        // Animation wieder aktivieren
        profileMenu.style.transition = 'transform 0.2s ease-out';
        
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
            }, 200);
        } else {
            // Menü zurück zur ursprünglichen Position
            profileMenu.style.transform = 'translateY(0)';
            setTimeout(() => {
                profileMenu.style.transition = '';
            }, 200);
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
