let usernameDebounceTimer = null;

function validateUsername() {
  const inputField = document.getElementById('username_input');
  if (!inputField) return;

  const usernameInput = inputField.value;
  const usernameCheck = document.getElementById('usernameCheck');
  const usernameX = document.getElementById('usernameX');
  const usernameAvailable = document.getElementById('usernameAvailable');
  const usernameNotAvailable = document.getElementById('usernameNotAvailable');

  if (usernameInput.length === 0) {
    inputField.style.borderColor = 'red';
    usernameCheck.style.display = 'none';
    usernameX.style.display = 'none';
    usernameAvailable.style.display = 'none';
    usernameNotAvailable.style.display = 'none';
    return;
  }

  // Muss zu constants.py passen: Mindestens 8 Zeichen und keine Leerzeichen!
  if (usernameInput.length < 8 || /\s/.test(usernameInput)) {
    inputField.style.borderColor = 'red';
    usernameCheck.style.display = 'none';
    usernameX.style.display = 'inline';
    usernameAvailable.style.display = 'none';
    usernameNotAvailable.textContent = 'Mindestens 8 Zeichen ohne Leerzeichen erforderlich';
    usernameNotAvailable.style.display = 'inline';
    return;
  }

  clearTimeout(usernameDebounceTimer);
  usernameDebounceTimer = setTimeout(() => {
    checkUsernameExists(usernameInput)
      .then(exists => {
        if (exists) {
          inputField.style.borderColor = 'red';
          usernameCheck.style.display = 'none';
          usernameX.style.display = 'inline';
          usernameAvailable.style.display = 'none';
          usernameNotAvailable.textContent = 'Benutzername ist bereits vergeben';
          usernameNotAvailable.style.display = 'inline';
        } else {
          inputField.style.borderColor = 'green';
          usernameCheck.style.display = 'inline';
          usernameX.style.display = 'none';
          usernameAvailable.style.display = 'inline';
          usernameNotAvailable.style.display = 'none';
        }
      })
      .catch(error => {
        console.error('Error:', error);
      });
  }, 300); // 300ms Debounce schont das Rate-Limit
}

function validatePassword(index) {
  const inputField = document.getElementById(`password_input_${index}`);
  if (!inputField) return;

  const passwordInput = inputField.value;
  let passwordCheck = document.getElementById('firstPWCheck');
  let passwordX = document.getElementById('firstPWX');
  const passwordNotTheSame = document.getElementById('passwordNotTheSame');

  if (index === 2) {
    passwordCheck = document.getElementById('secondPWCheck');
    passwordX = document.getElementById('secondPWX');
  }

  if (passwordInput.length === 0) {
    inputField.style.borderColor = 'red';
    passwordCheck.style.display = 'none';
    passwordX.style.display = 'none';
  } else if (passwordInput.length >= 8 && !/\s/.test(passwordInput)) {
    inputField.style.borderColor = 'green';
    passwordCheck.style.display = 'inline';
    passwordX.style.display = 'none';
  } else {
    inputField.style.borderColor = 'red';
    passwordCheck.style.display = 'none';
    passwordX.style.display = 'inline';
  }

  if (index === 1) {
    validatePassword(2);
  }

  if (index === 2) {
    const firstPasswordInput = document.getElementById('password_input_1')?.value || '';
    if (passwordInput.length >= 8 && !/\s/.test(passwordInput) && passwordInput === firstPasswordInput) {
      inputField.style.borderColor = 'green';
      passwordCheck.style.display = 'none';
      passwordX.style.display = 'none';
      passwordNotTheSame.style.display = 'none';
    } else {
      inputField.style.borderColor = 'red';
      passwordCheck.style.display = 'none';
      passwordX.style.display = 'inline';
      passwordNotTheSame.style.display = 'inline';
    }
  }
}

let lastUsernameValue = undefined;
let lastPassword1Value = undefined;
let lastPassword2Value = undefined;

function watchInputs() {
  const usernameEl = document.getElementById('username_input');
  const pw1El = document.getElementById('password_input_1');
  const pw2El = document.getElementById('password_input_2');

  // Beendet die Funktion sauber auf allen Seiten außer /register
  if (!usernameEl || !pw1El || !pw2El) {
    return;
  }

  usernameEl.addEventListener('input', () => {
    const currentUsernameValue = usernameEl.value;
    if (currentUsernameValue !== lastUsernameValue) {
      validateUsername();
      lastUsernameValue = currentUsernameValue;
    }
  });

  pw1El.addEventListener('input', () => {
    const currentPassword1Value = pw1El.value;
    if (currentPassword1Value !== lastPassword1Value) {
      validatePassword(1);
      lastPassword1Value = currentPassword1Value;
    }
  });

  pw2El.addEventListener('input', () => {
    const currentPassword2Value = pw2El.value;
    if (currentPassword2Value !== lastPassword2Value) {
      validatePassword(2);
      lastPassword2Value = currentPassword2Value;
    }
  });
}

async function checkUsernameExists(username) {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  const response = await fetch('/api/check-existence', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken || ''
    },
    body: JSON.stringify({
      type: 'username',
      value: username
    })
  });

  const data = await response.json();
  return data.exists;
}

document.addEventListener('DOMContentLoaded', watchInputs);