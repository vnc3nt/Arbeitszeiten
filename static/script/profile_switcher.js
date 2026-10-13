function selectProfile(select) {
    if (select.value === '__new__') {
        const name = window.prompt('Name des neuen Profils:');
        select.value = select.dataset.activeProfile;
        if (!name || !name.trim()) {
            return;
        }
        const maxhours = window.prompt('Monatsstunden für dieses Profil (z. B. 35,5):');
        if (!maxhours || !maxhours.trim()) {
            return;
        }

        const formData = new FormData();
        formData.append('name', name.trim());
        formData.append('maxhours', maxhours.trim());
        fetch('/profiles/create', {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'fetch' }
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
