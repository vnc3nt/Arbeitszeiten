function selectProfile(select) {
    if (select.value === '__new__') {
        const name = window.prompt('Name des neuen Profils:');
        select.value = select.dataset.activeProfile;
        if (!name || !name.trim()) {
            return;
        }
        const maxhours = window.prompt('Monatsstunden für dieses Profil:');
        if (!maxhours || !maxhours.trim()) {
            return;
        }

        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        const formData = new FormData();
        formData.append('name', name.trim());
        formData.append('maxhours', maxhours.trim());
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
            window.alert(error.message);
        });
        return;
    }

    select.form.submit();
}
