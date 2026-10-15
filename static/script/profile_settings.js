let dialogNormalShowModal = HTMLDialogElement.prototype.showModal;

let dialogCloseOnClick = (e) => {
    e.stopPropagation();
    let elem = e.target.closest("dialog");
    if (!elem) return;

    if (
        elem.offsetTop > e.y ||
        elem.offsetTop + elem.offsetHeight < e.y ||
        elem.offsetLeft - elem.offsetWidth / 2 > e.x ||
        elem.offsetLeft + elem.offsetWidth / 2 < e.x
    ) {
        elem.close();
    }
};

window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        let bg_modal = document.getElementById("modal-background");
        if (bg_modal) bg_modal.style.display = "none";
    }
}, true);

HTMLDialogElement.prototype.showModal = function () {
    let bg_modal = document.getElementById("modal-background");
    if (bg_modal) bg_modal.style.display = "block";
    dialogNormalShowModal.apply(this, arguments);
    this.addEventListener("click", dialogCloseOnClick);
};

let dialogNormalModalClose = HTMLDialogElement.prototype.close;
HTMLDialogElement.prototype.close = function () {
    let bg_modal = document.querySelector("#modal-background");
    if (bg_modal) bg_modal.style.display = "none";
    dialogNormalModalClose.apply(this, arguments);
    this.removeEventListener("click", dialogCloseOnClick);
};


window.addEventListener("DOMContentLoaded", (e) => {
    let change_user_name_btn = document.getElementById("changeUsernameBtn");
    let change_username_dialog = document.getElementById("change-user-name-dialog");
    if (!change_user_name_btn || !change_username_dialog) return;
    
    change_username_dialog.querySelector(".dialog-cancel-btn, input[type=reset]")?.addEventListener("click", (e) => {
        change_username_dialog.close();
    });

    change_username_dialog.querySelector("form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const isEn = document.documentElement.lang === "en";
        const form = change_username_dialog.querySelector("form");
        const newUsername = form.querySelector("input[name=new_username]").value.trim();
        const currentUsername = document.querySelector(".username")?.innerText.trim();
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
                alert(isEn ? "Username already exists" : "Benutzername existiert bereits");
            }
        } catch (error) {
            alert(isEn ? "Could not verify username" : "Benutzername konnte nicht geprüft werden");
        }
    });

    change_user_name_btn.addEventListener("click", (e) => {
        const currentName = document.querySelector(".username")?.innerText.trim() || "";
        const input = change_username_dialog.querySelector("input[name=new_username]");
        if (input) input.value = currentName;
        change_username_dialog.showModal();
        if (input) input.focus();
    });
});

window.addEventListener("DOMContentLoaded", () => {
    const manageProfilesBtn = document.getElementById("manageProfilesBtn");
    const manageProfilesDialog = document.getElementById("manage-profiles-dialog");
    if (!manageProfilesDialog) return;

    if (manageProfilesBtn) {
        manageProfilesBtn.addEventListener("click", () => manageProfilesDialog.showModal());
    }

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

    manageProfilesDialog.querySelectorAll(".profile-management-row").forEach(row => {
        const input = row.querySelector(".profile-name-input");
        const profileId = row.querySelector("input[name=profile_id]")?.value;
        if (!input || !profileId) return;

        // Prevent standard form submission (e.g. on Enter)
        row.addEventListener("submit", (e) => e.preventDefault());

        // 1. Auto-save profile name on blur or enter
        const saveName = async () => {
            const originalName = input.getAttribute("data-original-name");
            const newName = input.value.trim();

            if (!newName) {
                input.value = originalName;
                return;
            }

            if (newName === originalName) {
                return;
            }

            try {
                const formData = new FormData();
                formData.append("csrf_token", csrfToken || "");
                formData.append("profile_id", profileId);
                formData.append("profile_action", "rename");
                formData.append("name", newName);

                const response = await fetch("/profiles/manage", {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "fetch"
                    },
                    body: formData
                });

                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || "Fehler beim Umbenennen");
                }

                input.setAttribute("data-original-name", newName);
                input.classList.add("save-success");
                setTimeout(() => input.classList.remove("save-success"), 1200);
            } catch (err) {
                input.classList.add("save-error");
                setTimeout(() => input.classList.remove("save-error"), 1500);
                alert(err.message || "Profil konnte nicht umbenannt werden");
                input.value = originalName;
            }
        };

        input.addEventListener("blur", saveName);
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                input.blur();
            } else if (e.key === "Escape") {
                input.value = input.getAttribute("data-original-name");
                input.blur();
            }
        });

        // 2. AJAX for visibility toggle
        const visBtn = row.querySelector(".visibility-btn");
        if (visBtn) {
            visBtn.addEventListener("click", async (e) => {
                e.preventDefault();
                try {
                    const formData = new FormData();
                    formData.append("csrf_token", csrfToken || "");
                    formData.append("profile_id", profileId);
                    formData.append("profile_action", "toggle-visibility");

                    const response = await fetch("/profiles/manage", {
                        method: "POST",
                        headers: {
                            "X-Requested-With": "fetch"
                        },
                        body: formData
                    });

                    const data = await response.json();
                    if (!response.ok) {
                        throw new Error(data.error || "Fehler beim Ändern der Sichtbarkeit");
                    }

                    const isVisible = data.visible;
                    const eyeOpen = visBtn.querySelector(".eye-open-icon");
                    const eyeClosed = visBtn.querySelector(".eye-closed-icon");

                    if (isVisible) {
                        row.classList.remove("is-hidden");
                        visBtn.classList.remove("is-hidden");
                        visBtn.title = "Profil ausblenden";
                        visBtn.setAttribute("aria-label", "Profil ausblenden");
                        if (eyeOpen) eyeOpen.style.display = "";
                        if (eyeClosed) eyeClosed.style.display = "none";
                    } else {
                        row.classList.add("is-hidden");
                        visBtn.classList.add("is-hidden");
                        visBtn.title = "Profil einblenden";
                        visBtn.setAttribute("aria-label", "Profil einblenden");
                        if (eyeOpen) eyeOpen.style.display = "none";
                        if (eyeClosed) eyeClosed.style.display = "";
                    }
                } catch (err) {
                    alert(err.message || "Sichtbarkeit konnte nicht geändert werden");
                }
            });
        }

        // 3. AJAX for delete
        const delBtn = row.querySelector(".delete-btn");
        if (delBtn) {
            delBtn.addEventListener("click", async (e) => {
                e.preventDefault();
                if (!confirm("Arbeitsprofil wirklich löschen?")) {
                    return;
                }

                try {
                    const formData = new FormData();
                    formData.append("csrf_token", csrfToken || "");
                    formData.append("profile_id", profileId);
                    formData.append("profile_action", "delete");

                    const response = await fetch("/profiles/manage", {
                        method: "POST",
                        headers: {
                            "X-Requested-With": "fetch"
                        },
                        body: formData
                    });

                    const data = await response.json();
                    if (!response.ok) {
                        throw new Error(data.error || "Fehler beim Löschen des Profils");
                    }

                    row.style.transition = "all 0.25s ease-out";
                    row.style.opacity = "0";
                    row.style.transform = "scale(0.95)";
                    setTimeout(() => row.remove(), 250);
                } catch (err) {
                    alert(err.message || "Profil konnte nicht gelöscht werden");
                }
            });
        }
    });

    // 4. Drag & Drop reordering
    const list = manageProfilesDialog.querySelector(".manage-profiles-list");
    if (list) {
        let draggedRow = null;
        let initialOrderIds = [];

        const getOrderIds = () => {
            return Array.from(list.querySelectorAll(".profile-management-row"))
                .map(r => r.getAttribute("data-profile-id"))
                .filter(Boolean);
        };

        initialOrderIds = getOrderIds();

        const saveOrder = async () => {
            const currentOrder = getOrderIds();
            if (currentOrder.length === 0) return;
            if (JSON.stringify(currentOrder) === JSON.stringify(initialOrderIds)) {
                return;
            }

            try {
                const formData = new FormData();
                formData.append("csrf_token", csrfToken || "");
                formData.append("profile_action", "reorder");
                formData.append("order", JSON.stringify(currentOrder));

                const response = await fetch("/profiles/manage", {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "fetch"
                    },
                    body: formData
                });

                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || "Fehler beim Speichern der Reihenfolge");
                }

                initialOrderIds = currentOrder;

                // Reorder dropdown options in header/home if present in DOM
                const selector = document.getElementById("profile-selector");
                if (selector) {
                    const newProfileOption = selector.querySelector('option[value="__new__"]');
                    currentOrder.forEach(id => {
                        const opt = selector.querySelector(`option[value="${id}"]`);
                        if (opt) {
                            if (newProfileOption) {
                                selector.insertBefore(opt, newProfileOption);
                            } else {
                                selector.appendChild(opt);
                            }
                        }
                    });
                }
            } catch (err) {
                console.error(err);
                alert(err.message || "Reihenfolge konnte nicht gespeichert werden");
            }
        };

        const clearDragStyles = () => {
            list.querySelectorAll(".profile-management-row").forEach(r => {
                r.classList.remove("is-dragging", "drag-over-top", "drag-over-bottom");
            });
        };

        list.querySelectorAll(".profile-management-row").forEach(row => {
            const handle = row.querySelector(".drag-handle");
            if (!handle) return;

            // Make draggable on handle interaction
            handle.addEventListener("mouseenter", () => {
                row.setAttribute("draggable", "true");
            });
            handle.addEventListener("mouseleave", () => {
                if (!draggedRow) {
                    row.removeAttribute("draggable");
                }
            });

            row.addEventListener("dragstart", (e) => {
                draggedRow = row;
                initialOrderIds = getOrderIds();
                row.classList.add("is-dragging");
                e.dataTransfer.effectAllowed = "move";
                e.dataTransfer.setData("text/plain", row.getAttribute("data-profile-id"));
            });

            row.addEventListener("dragend", () => {
                row.removeAttribute("draggable");
                draggedRow = null;
                clearDragStyles();
            });
        });

        list.addEventListener("dragover", (e) => {
            e.preventDefault();
            if (!draggedRow) return;
            e.dataTransfer.dropEffect = "move";

            const targetRow = e.target.closest(".profile-management-row");
            if (!targetRow || targetRow === draggedRow) return;

            const rect = targetRow.getBoundingClientRect();
            const isTopHalf = (e.clientY - rect.top) < (rect.height / 2);

            list.querySelectorAll(".profile-management-row").forEach(r => {
                if (r !== targetRow) {
                    r.classList.remove("drag-over-top", "drag-over-bottom");
                }
            });

            if (isTopHalf) {
                targetRow.classList.add("drag-over-top");
                targetRow.classList.remove("drag-over-bottom");
            } else {
                targetRow.classList.add("drag-over-bottom");
                targetRow.classList.remove("drag-over-top");
            }
        });

        list.addEventListener("dragleave", (e) => {
            if (!list.contains(e.relatedTarget)) {
                clearDragStyles();
            }
        });

        list.addEventListener("drop", async (e) => {
            e.preventDefault();
            if (!draggedRow) return;

            const targetRow = e.target.closest(".profile-management-row");
            if (targetRow && targetRow !== draggedRow) {
                const rect = targetRow.getBoundingClientRect();
                const isTopHalf = (e.clientY - rect.top) < (rect.height / 2);

                if (isTopHalf) {
                    list.insertBefore(draggedRow, targetRow);
                } else {
                    list.insertBefore(draggedRow, targetRow.nextSibling);
                }
            }

            clearDragStyles();
            draggedRow = null;
            await saveOrder();
        });

        // Touch support for touch devices
        let touchDraggedRow = null;

        list.querySelectorAll(".drag-handle").forEach(handle => {
            handle.addEventListener("touchstart", (e) => {
                const row = handle.closest(".profile-management-row");
                if (!row) return;
                touchDraggedRow = row;
                initialOrderIds = getOrderIds();
                row.classList.add("is-dragging");
            }, { passive: true });

            handle.addEventListener("touchmove", (e) => {
                if (!touchDraggedRow) return;
                e.preventDefault();
                const touch = e.touches[0];
                const elementUnderPoint = document.elementFromPoint(touch.clientX, touch.clientY);
                const targetRow = elementUnderPoint?.closest(".profile-management-row");

                list.querySelectorAll(".profile-management-row").forEach(r => {
                    r.classList.remove("drag-over-top", "drag-over-bottom");
                });

                if (targetRow && targetRow !== touchDraggedRow) {
                    const rect = targetRow.getBoundingClientRect();
                    const isTopHalf = (touch.clientY - rect.top) < (rect.height / 2);
                    if (isTopHalf) {
                        targetRow.classList.add("drag-over-top");
                    } else {
                        targetRow.classList.add("drag-over-bottom");
                    }
                }
            }, { passive: false });

            handle.addEventListener("touchend", async () => {
                if (!touchDraggedRow) return;
                const rowWithOver = list.querySelector(".drag-over-top, .drag-over-bottom");
                if (rowWithOver) {
                    if (rowWithOver.classList.contains("drag-over-top")) {
                        list.insertBefore(touchDraggedRow, rowWithOver);
                    } else {
                        list.insertBefore(touchDraggedRow, rowWithOver.nextSibling);
                    }
                }
                clearDragStyles();
                touchDraggedRow = null;
                await saveOrder();
            });

            handle.addEventListener("touchcancel", () => {
                clearDragStyles();
                touchDraggedRow = null;
            });
        });
    }
});

window.addEventListener("DOMContentLoaded", (e) => {
    let delete_account_btn = document.getElementById("deleteAccountBtn");
    let delete_acc_dialog = document.getElementById("delete-account-dialog");
    if (!delete_account_btn || !delete_acc_dialog) return;

    delete_acc_dialog.querySelector(".dialog-cancel-btn, input[type=reset]")?.addEventListener("click", (e) => {
        delete_acc_dialog.close();
    });

    delete_account_btn.addEventListener("click", (e) => {
        delete_acc_dialog.showModal();
        delete_acc_dialog.querySelector("input#password")?.focus();
    });
});


window.addEventListener("DOMContentLoaded", (e) => {
    let change_password_btn = document.getElementById("changePasswordBtn");
    let change_password_dialog = document.getElementById("change-password-dialog");
    if (!change_password_btn || !change_password_dialog) return;

    change_password_dialog.querySelector(".dialog-cancel-btn, input[type=reset]")?.addEventListener("click", (e) => {
        change_password_dialog.close();
    });

    change_password_btn.addEventListener("click", (e) => {
        change_password_dialog.showModal();
        change_password_dialog.querySelector("input")?.focus();
    });
});

window.addEventListener("DOMContentLoaded", () => {
    const langControl = document.getElementById("language-segmented-control");
    if (!langControl) return;

    langControl.querySelectorAll(".theme-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
            const lang = btn.getAttribute("data-lang-value");
            if (!lang) return;

            langControl.querySelectorAll(".theme-btn").forEach(b => b.classList.remove("is-active"));
            btn.classList.add("is-active");

            const formData = new FormData();
            formData.append("language", lang);
            try {
                const response = await fetch("/set-language", {
                    method: "POST",
                    headers: { "X-Requested-With": "fetch" },
                    body: formData
                });
                if (response.ok) {
                    // Seite neu laden, damit alle Übersetzungen sofort greifen
                    window.location.reload();
                }
            } catch (e) {
                console.error("Sprache konnte nicht gespeichert werden", e);
            }
        });
    });
});

window.addEventListener("DOMContentLoaded", () => {
    const themeControl = document.getElementById("theme-segmented-control") || document.querySelector(".theme-segmented-control");
    if (!themeControl) return;

    // Sync button state with current active theme
    const activeTheme = localStorage.getItem("app-theme") || document.documentElement.getAttribute("data-theme") || "auto";
    themeControl.querySelectorAll(".theme-btn").forEach(btn => {
        if (btn.getAttribute("data-theme-value") === activeTheme) {
            btn.classList.add("is-active");
        } else {
            btn.classList.remove("is-active");
        }
    });

    themeControl.querySelectorAll(".theme-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const theme = btn.getAttribute("data-theme-value");
            if (!theme) return;

            themeControl.querySelectorAll(".theme-btn").forEach(b => b.classList.remove("is-active"));
            btn.classList.add("is-active");

            // Apply theme classes immediately to documentElement
            if (theme === "dark") {
                document.documentElement.classList.add("dark-mode");
                document.documentElement.classList.remove("light-mode");
            } else if (theme === "light") {
                document.documentElement.classList.add("light-mode");
                document.documentElement.classList.remove("dark-mode");
            } else {
                document.documentElement.classList.remove("dark-mode", "light-mode");
            }
            document.documentElement.setAttribute("data-theme", theme);

            if (typeof setDynamicCardBackground === "function") {
                setDynamicCardBackground();
            }

            // Persist locally
            try {
                localStorage.setItem("app-theme", theme);
            } catch (e) {
                console.error(e);
            }

            // Persist to server
            const formData = new FormData();
            formData.append("theme", theme);
            fetch("/set-theme", {
                method: "POST",
                headers: { "X-Requested-With": "fetch" },
                body: formData
            }).catch(console.error);
        });
    });
});

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

    changeProfilePicDialog.querySelector(".dialog-cancel-btn, input[type=reset]")?.addEventListener("click", () => {
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
