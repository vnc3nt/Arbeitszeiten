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
    } else {
        const edgeColor = hexToRgba(color, 0.5);
        overlay.style.setProperty('--profile-overlay-color', edgeColor);
    }
}

function selectProfile(select) {
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

