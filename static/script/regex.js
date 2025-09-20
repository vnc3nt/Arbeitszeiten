function validateUsername() {
  const inputField = document.getElementById('username_input');
  const usernameInput = document.getElementById('username_input').value;
  const usernameCheck = document.getElementById('usernameCheck');
  const usernameX = document.getElementById('usernameX');
  const usernameAvailable = document.getElementById('usernameAvailable');
  const usernameNotAvailable = document.getElementById('usernameNotAvailable');


  if (usernameInput.length === 0) {
    inputField.style.borderColor ='red';
    usernameCheck.style.display = 'none';
    usernameX.style.display = 'none';
    usernameAvailable.style.display = 'none';
    usernameNotAvailable.style.display = 'none';
  }

  else if (!/\s/.test(usernameInput)) {

    checkUsernameExists(usernameInput)
      .then(exists => {
        if (exists) {
          console.log('Username exists');
          inputField.style.borderColor ='red';
          usernameCheck.style.display = 'none';
          usernameX.style.display = 'inline';
          usernameAvailable.style.display = 'none';
          usernameNotAvailable.style.display = 'inline';
          
        } else {
          console.log('Username does not exist');
          inputField.style.borderColor ='green';
          usernameCheck.style.display = 'inline';
          usernameX.style.display = 'none';
          usernameAvailable.style.display = 'inline';
          usernameNotAvailable.style.display = 'none';
        }
      })
      .catch(error => {
        console.error('Error:', error);
      });
  } else {
    inputField.style.borderColor ='red';
    usernameCheck.style.display = 'none';
    usernameX.style.display = 'inline';
    usernameAvailable.style.display = 'none';
    usernameNotAvailable.style.display = 'inline';
  }
}

function validatePassword(index) {
  const inputField = document.getElementById(`password_input_${index}`);
  const passwordInput = document.getElementById(`password_input_${index}`).value;
  let passwordCheck = document.getElementById(`firstPWCheck`);
  let passwordX = document.getElementById(`firstPWX`);
  const passwordNotTheSame = document.getElementById('passwordNotTheSame');

  if (index === 2) {
    passwordCheck = document.getElementById(`secondPWCheck`);
    passwordX = document.getElementById(`secondPWX`);
  }
  

  if (passwordInput.length === 0) {
    inputField.style.borderColor ='red';
    passwordCheck.style.display = 'none';
    passwordX.style.display = 'none';
  }

  else if (passwordInput.length >= 8 && !/\s/.test(passwordInput)) {
    inputField.style.borderColor ='green';
    passwordCheck.style.display = 'inline';
    passwordX.style.display = 'none';

  } else {
    inputField.style.borderColor ='red';
    passwordCheck.style.display = 'none';
    passwordX.style.display = 'inline';
  }
  
  if (index === 1) {
    validatePassword(2);
  }

  if (index === 2) {
    const firstPasswordInput = document.getElementById('password_input_1').value;
    if (passwordInput.length >= 8 && !/\s/.test(passwordInput) && passwordInput === firstPasswordInput) {
      inputField.style.borderColor ='green';
      passwordCheck.style.display = 'none';
      passwordX.style.display = 'none';
      passwordNotTheSame.style.display = 'none';
    }
    else {
      inputField.style.borderColor ='red';
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
  document.getElementById('username_input').addEventListener('input', () => {
    const currentUsernameValue = document.getElementById('username_input').value;
    console.debug("yesss");
    if (currentUsernameValue !== lastUsernameValue) {
      validateUsername();
      lastUsernameValue = currentUsernameValue;
    }
  });

  document.getElementById('password_input_1').addEventListener('input', () => {
    const currentPassword1Value = document.getElementById('password_input_1').value;
    if (currentPassword1Value !== lastPassword1Value) {
      validatePassword(1);
      lastPassword1Value = currentPassword1Value;
    }
  });

  document.getElementById('password_input_2').addEventListener('input', () => {
    const currentPassword2Value = document.getElementById('password_input_2').value;
    if (currentPassword2Value !== lastPassword2Value) {
      validatePassword(2);
      lastPassword2Value = currentPassword2Value;
    }
  });
}

function validateForm() {
  validateUsername();
  validatePassword(1);
  validatePassword(2);

  const usernameCheck = document.getElementById('usernameCheck').style.display === 'inline';
  const firstPWCheck = document.getElementById('firstPWCheck').style.display === 'inline';
  const secondPWCheck = document.getElementById('secondPWCheck').style.display === 'inline';

  return usernameCheck && firstPWCheck && secondPWCheck;
}

async function checkUsernameExists(username) {
  const response = await fetch('/api/check-existence', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      type: 'username',
      value: username
    })
  });
  

  const data = await response.json();
  return data.exists;
}

// Startet die Überwachung der Eingabefelder, wenn das Dokument geladen ist
document.addEventListener('DOMContentLoaded', watchInputs);