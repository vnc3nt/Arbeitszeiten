function hexToRgba(hex, alpha) {
    if (!hex) return 'transparent';
    let clean = hex.replace('#', '').trim();
    if (clean.length === 3) {
        clean = clean.split('').map(c => c + c).join('');
    }
    if (clean.length !== 6) return 'transparent';
    const r = parseInt(clean.substring(0, 2), 16);
    const g = parseInt(clean.substring(2, 4), 16);
    const b = parseInt(clean.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function updateVignetteOverlay(color) {
    const overlay = document.getElementById('profile-vignette-overlay');
    if (!overlay) return;
    if (!color) {
        overlay.style.removeProperty('--profile-overlay-color');
        overlay.style.background = 'radial-gradient(ellipse at center, transparent 35%, transparent 100%)';
    } else {
        const edgeColor = hexToRgba(color, 0.5);
        overlay.style.setProperty('--profile-overlay-color', edgeColor);
        overlay.style.background = `radial-gradient(ellipse at center, transparent 35%, ${edgeColor} 100%)`;
    }
}

function openNewProfileModal() {
    const modal = document.getElementById('newProfileModal');
    if (!modal) return;
    modal.style.display = 'flex';
    const nameInput = document.getElementById('new-profile-name-input');
    if (nameInput) {
        nameInput.value = '';
        setTimeout(() => nameInput.focus(), 50);
    }
    const maxHoursInput = document.getElementById('new-profile-maxhours-input');
    if (maxHoursInput) maxHoursInput.value = '160';
    const colorInput = document.getElementById('new-profile-color-input');
    if (colorInput) {
        colorInput.value = '#7300ff';
        const hexDisplay = document.getElementById('new-profile-color-hex');
        if (hexDisplay) hexDisplay.textContent = '#7300ff';
    }
}

function closeNewProfileModal() {
    const modal = document.getElementById('newProfileModal');
    if (modal) modal.style.display = 'none';
    const select = document.getElementById('profile-selector');
    if (select && select.dataset.activeProfile) {
        select.value = select.dataset.activeProfile;
    }
}

function submitNewProfile(event) {
    if (event) event.preventDefault();
    const nameInput = document.getElementById('new-profile-name-input');
    const maxHoursInput = document.getElementById('new-profile-maxhours-input');
    const colorInput = document.getElementById('new-profile-color-input');

    const name = nameInput ? nameInput.value.trim() : '';
    const maxhours = maxHoursInput ? maxHoursInput.value.trim() : '';
    const color = colorInput ? colorInput.value : '';

    if (!name) {
        alert('Bitte einen Namen für das Profil eingeben');
        return;
    }
    if (!maxhours) {
        alert('Bitte Monatsstunden angeben');
        return;
    }

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    const formData = new FormData();
    formData.append('name', name);
    formData.append('maxhours', maxhours);
    if (color) {
        formData.append('color', color);
    }

    fetch('/profiles/create', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'fetch',
            'X-CSRFToken': csrfToken || ''
        }
    }).then((response) => {
        if (!response.ok) {
            return response.json().then((body) => {
                throw new Error(body.error || 'Profil konnte nicht erstellt werden');
            });
        }
        window.location.href = response.url;
    }).catch((error) => {
        alert(error.message);
    });
}

function selectProfile(select) {
    if (select.value === '__new__') {
        openNewProfileModal();
        return;
    }

    const selectedOption = select.options[select.selectedIndex];
    const profileColor = selectedOption?.getAttribute('data-color');
    if (profileColor) {
        updateVignetteOverlay(profileColor);
    } else {
        updateVignetteOverlay(null);
    }

    select.form.submit();
}

document.addEventListener('DOMContentLoaded', () => {
    const select = document.getElementById('profile-selector');
    if (select) {
        const selectedOption = select.options[select.selectedIndex];
        const profileColor = selectedOption?.getAttribute('data-color');
        if (profileColor) {
            updateVignetteOverlay(profileColor);
        }
    }
});

