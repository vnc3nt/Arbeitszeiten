# -*- coding: utf-8 -*-
"""Internationalization (i18n) translation dictionaries and helpers for Arbeitszeiten."""

SUPPORTED_LANGUAGES = {
    'de': 'Deutsch',
    'en': 'English'
}

DEFAULT_LANGUAGE = 'de'

MONTH_NAMES = {
    'de': {
        1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
        5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
    },
    'en': {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
}

TRANSLATIONS = {
    'de': {
        # Common
        'common.cancel': 'Abbrechen',
        'common.save': 'Speichern',
        'common.close': 'Schließen',
        'common.delete': 'Löschen',
        'common.edit': 'Ändern',
        'common.back': 'Zur Startseite',
        'common.back_home': 'Zur Startseite',
        'common.back_simple': 'Zurück',
        'common.today': 'Heute',
        'common.total': 'Insgesamt',
        'common.error': 'Fehler',
        'common.success': 'Erfolgreich',
        
        # Menu
        'menu.donate': 'Spenden',
        'menu.settings': 'Einstellungen',
        'menu.logout': 'Abmelden',
        'menu.impressum': 'Impressum',
        'menu.dpa': 'Datenschutzerklärung',
        'menu.agb': 'AGB',

        # Impressum
        'impressum.title': 'Impressum',
        'impressum.ddg_title': 'Angaben gemäß § 5 Digitale-Dienste-Gesetz (DDG):',
        'impressum.contact_title': 'Kontakt:',
        'impressum.phone_label': 'Telefon:',
        'impressum.mstv_title': 'Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV:',
        'impressum.legal_docs_title': 'Datenschutz & AGB:',
        'impressum.dpa_text': 'Unsere Datenschutzerklärung finden Sie {link}.',
        'impressum.agb_text': 'Unsere Allgemeinen Geschäftsbedingungen (AGB) finden Sie {link}.',
        'impressum.here': 'hier',
        'impressum.country': 'Deutschland',
        
        # Home
        'home.new_profile': '+ Neues Profil erstellen',
        'home.max_hours_title': 'Maximale Stunden pro Monat',
        'home.max_hours_hint': 'Bitte geben Sie die Stundenanzahl pro Monat ein (z.B. 35, 35.5 oder 35,5)',
        'home.overview_title': 'Arbeitszeiten-Übersicht',
        'home.overview_loading': 'Übersicht wird bei Bedarf geladen.',
        
        # Settings
        'settings.title': 'Kontoeinstellungen',
        'settings.subtitle': 'Verwalte dein Konto, dein Profilbild und deine Arbeitsprofile.',
        'settings.account.title': 'Konto',
        'settings.account.desc': 'Persönliche Kontodaten, Profilbild und Sicherheit',
        'settings.account.change_avatar': 'Profilbild ändern',
        'settings.account.change_username': 'Benutzernamen ändern',
        'settings.account.change_password': 'Passwort ändern',
        'settings.appearance.title': 'Darstellung',
        'settings.appearance.desc': 'Design- und Spracheinstellungen',
        'settings.appearance.change_language': 'Sprache ändern',
        'settings.appearance.theme': 'Design',
        'settings.appearance.theme_auto': 'Automatisch',
        'settings.appearance.theme_dark': 'Darkmode',
        'settings.appearance.theme_light': 'Lightmode',
        'settings.profiles.title': 'Arbeitsprofile',
        'settings.profiles.desc': 'Profile sortieren, umbenennen, ausblenden oder löschen',
        'settings.profiles.manage': 'Profile bearbeiten',
        'settings.danger.title': 'Account',
        'settings.danger.desc': 'Diese Aktion kann nicht rückgängig gemacht werden.',
        'settings.danger.delete': 'Account löschen',
        
        # Dialogs
        'dialog.username.title': 'Benutzernamen ändern',
        'dialog.username.desc': 'Wähle einen neuen Benutzernamen für deinen Account',
        'dialog.username.placeholder': 'Neuer Benutzername',
        'dialog.username.submit': 'Speichern',
        
        'dialog.password.title': 'Passwort ändern',
        'dialog.password.desc': 'Verwende mindestens 8 Zeichen für ein sicheres Passwort',
        'dialog.password.current': 'Aktuelles Passwort',
        'dialog.password.new': 'Neues Passwort',
        'dialog.password.confirm': 'Neues Passwort bestätigen',
        'dialog.password.submit': 'Passwort aktualisieren',
        
        'dialog.avatar.title': 'Profilbild ändern',
        'dialog.avatar.desc': 'Lade ein neues Profilbild hoch (PNG, JPG oder WEBP bis 2 MB)',
        'dialog.avatar.choose': 'Bild auswählen',
        'dialog.avatar.hint': 'Erlaubt sind PNG, JPG und WEBP bis 2 MB. Das Bild wird quadratisch zugeschnitten.',
        'dialog.avatar.zoom': 'Zoom',
        'dialog.avatar.move_hint': 'Bild im Ausschnitt verschieben',
        'dialog.avatar.reset': 'Standardbild wiederherstellen',
        'dialog.avatar.submit': 'Speichern',
        
        'dialog.language.title': 'Sprache ändern',
        'dialog.language.desc': 'Wähle deine bevorzugte Sprache für die Benutzeroberfläche',
        'dialog.language.de': 'Deutsch',
        'dialog.language.en': 'English',
        'dialog.language.submit': 'Übernehmen',
        
        'dialog.profiles.title': 'Arbeitsprofile bearbeiten',
        'dialog.profiles.desc': 'Reihenfolge per Ziehen ändern, Namen direkt im Feld bearbeiten',
        'dialog.profiles.placeholder': 'Profilname',
        'dialog.profiles.color_hint': 'Profilfarbe ändern',
        'dialog.profiles.new_title': 'Neues Arbeitsprofil',
        'dialog.profiles.name': 'Name des Profils',
        'dialog.profiles.maxhours': 'Monatsstunden',
        'dialog.profiles.color': 'Farbe',
        'dialog.profiles.drag_hint': 'Reihenfolge durch Ziehen ändern',
        'dialog.profiles.show': 'Profil einblenden',
        'dialog.profiles.hide': 'Profil ausblenden',
        'dialog.profiles.delete': 'Profil löschen',
        'dialog.profiles.delete_confirm': 'Arbeitsprofil wirklich löschen?',
        
        'dialog.delete_acc.title': 'Account löschen',
        'dialog.delete_acc.desc': 'Gib dein Passwort zur Bestätigung ein. Alle Daten werden unwiderruflich gelöscht.',
        'dialog.delete_acc.password': 'Passwort eingeben',
        'dialog.delete_acc.submit': 'Account unwiderruflich löschen',
        
        # Auth
        'auth.login': 'Einloggen',
        'auth.register': 'Registrieren',
        'auth.username': 'Benutzername',
        'auth.password': 'Passwort',
        'auth.password_repeat': 'Passwort wiederholen',
        'auth.terms_prefix': 'Ich habe die',
        'auth.terms_dpa': 'Datenschutzerklärung',
        'auth.terms_and': 'und',
        'auth.terms_agb': 'AGB',
        'auth.terms_suffix': 'gelesen und stimme ihnen zu.',
    },
    'en': {
        # Common
        'common.cancel': 'Cancel',
        'common.save': 'Save',
        'common.close': 'Close',
        'common.delete': 'Delete',
        'common.edit': 'Change',
        'common.back': 'Back to Home',
        'common.back_home': 'Back to Home',
        'common.back_simple': 'Back',
        'common.today': 'Today',
        'common.total': 'Total',
        'common.error': 'Error',
        'common.success': 'Success',
        
        # Menu
        'menu.donate': 'Donate',
        'menu.settings': 'Settings',
        'menu.logout': 'Log Out',
        'menu.impressum': 'Legal Notice',
        'menu.dpa': 'Privacy Policy',
        'menu.agb': 'Terms of Service',

        # Impressum
        'impressum.title': 'Legal Notice',
        'impressum.ddg_title': 'Information pursuant to § 5 Digital Services Act (DDG):',
        'impressum.contact_title': 'Contact:',
        'impressum.phone_label': 'Phone:',
        'impressum.mstv_title': 'Responsible for content pursuant to § 18 (2) MStV:',
        'impressum.legal_docs_title': 'Privacy Policy & Terms of Service:',
        'impressum.dpa_text': 'You can find our Privacy Policy {link}.',
        'impressum.agb_text': 'You can find our Terms of Service (AGB) {link}.',
        'impressum.here': 'here',
        'impressum.country': 'Germany',
        
        # Home
        'home.new_profile': '+ Create new profile',
        'home.max_hours_title': 'Maximum Hours per Month',
        'home.max_hours_hint': 'Please enter the monthly target hours (e.g. 35 or 35.5)',
        'home.overview_title': 'Work Hours Overview',
        'home.overview_loading': 'Overview will load on demand.',
        
        # Settings
        'settings.title': 'Account Settings',
        'settings.subtitle': 'Manage your account, profile picture and work profiles.',
        'settings.account.title': 'Account',
        'settings.account.desc': 'Personal account details, profile picture and security',
        'settings.account.change_avatar': 'Change Profile Picture',
        'settings.account.change_username': 'Change Username',
        'settings.account.change_password': 'Change Password',
        'settings.appearance.title': 'Appearance',
        'settings.appearance.desc': 'Theme and language settings',
        'settings.appearance.change_language': 'Change Language',
        'settings.appearance.theme': 'Theme',
        'settings.appearance.theme_auto': 'Automatic',
        'settings.appearance.theme_dark': 'Dark mode',
        'settings.appearance.theme_light': 'Light mode',
        'settings.profiles.title': 'Work Profiles',
        'settings.profiles.desc': 'Reorder, rename, hide or delete profiles',
        'settings.profiles.manage': 'Manage Profiles',
        'settings.danger.title': 'Danger Zone',
        'settings.danger.desc': 'This action cannot be undone.',
        'settings.danger.delete': 'Delete Account',
        
        # Dialogs
        'dialog.username.title': 'Change Username',
        'dialog.username.desc': 'Choose a new username for your account',
        'dialog.username.placeholder': 'New username',
        'dialog.username.submit': 'Save',
        
        'dialog.password.title': 'Change Password',
        'dialog.password.desc': 'Use at least 8 characters for a secure password',
        'dialog.password.current': 'Current password',
        'dialog.password.new': 'New password',
        'dialog.password.confirm': 'Confirm new password',
        'dialog.password.submit': 'Update Password',
        
        'dialog.avatar.title': 'Change Profile Picture',
        'dialog.avatar.desc': 'Upload a new profile picture (PNG, JPG or WEBP up to 2 MB)',
        'dialog.avatar.choose': 'Choose Image',
        'dialog.avatar.hint': 'PNG, JPG and WEBP up to 2 MB allowed. Image will be cropped square.',
        'dialog.avatar.zoom': 'Zoom',
        'dialog.avatar.move_hint': 'Drag image to adjust position',
        'dialog.avatar.reset': 'Restore Default Picture',
        'dialog.avatar.submit': 'Save',
        
        'dialog.language.title': 'Change Language',
        'dialog.language.desc': 'Choose your preferred language for the interface',
        'dialog.language.de': 'German (Deutsch)',
        'dialog.language.en': 'English',
        'dialog.language.submit': 'Apply',
        
        'dialog.profiles.title': 'Manage Work Profiles',
        'dialog.profiles.desc': 'Drag to reorder, edit names directly in the field',
        'dialog.profiles.placeholder': 'Profile name',
        'dialog.profiles.color_hint': 'Change profile color',
        'dialog.profiles.new_title': 'New Work Profile',
        'dialog.profiles.name': 'Profile Name',
        'dialog.profiles.maxhours': 'Monthly Hours',
        'dialog.profiles.color': 'Color',
        'dialog.profiles.drag_hint': 'Drag to reorder',
        'dialog.profiles.show': 'Show profile',
        'dialog.profiles.hide': 'Hide profile',
        'dialog.profiles.delete': 'Delete profile',
        'dialog.profiles.delete_confirm': 'Are you sure you want to delete this profile?',
        
        'dialog.delete_acc.title': 'Delete Account',
        'dialog.delete_acc.desc': 'Enter your password to confirm. All your data will be permanently deleted.',
        'dialog.delete_acc.password': 'Enter password',
        'dialog.delete_acc.submit': 'Permanently Delete Account',
        
        # Auth
        'auth.login': 'Log In',
        'auth.register': 'Register',
        'auth.username': 'Username',
        'auth.password': 'Password',
        'auth.password_repeat': 'Repeat password',
        'auth.terms_prefix': 'I have read and agree to the',
        'auth.terms_dpa': 'Privacy Policy',
        'auth.terms_and': 'and',
        'auth.terms_agb': 'Terms of Service',
        'auth.terms_suffix': '.',
    }
}


def get_translation(key: str, lang: str = 'de', **kwargs) -> str:
    """Retrieve translated string with fallback to German and then key."""
    lang_translations = TRANSLATIONS.get(lang, TRANSLATIONS['de'])
    text = lang_translations.get(key)
    if text is None:
        text = TRANSLATIONS['de'].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def get_month_name(month: int, lang: str = 'de') -> str:
    """Retrieve localized month name."""
    months = MONTH_NAMES.get(lang, MONTH_NAMES['de'])
    return months.get(month, '')
