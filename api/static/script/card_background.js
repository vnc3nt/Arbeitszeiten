function setDynamicCardBackground() {
  const card = document.getElementById('total-hours-card');
  const totalHours = parseFloat(card.getAttribute('data-hours'));

  // Basisgrau für 0 (dunkles Grau)
  const gray = { r: 68, g: 68, b: 68 };

  // Maximalroter Farbton (für -50 Stunden)
  const maxRed = { r: 220, g: 30, b: 30 };

  // Maximalgrüner Farbton (für +30 Stunden)
  const maxGreen = { r: 30, g: 180, b: 60 };

  let r, g, b;

  if (totalHours === 0) {
    r = gray.r; g = gray.g; b = gray.b;
  } else if (totalHours < 0) {
    // Interpolieren von Grau zu MaxRot je nach Abstand bis -50h
    const intensity = Math.min(Math.abs(totalHours) / 50, 1);
    r = Math.round(gray.r + intensity * (maxRed.r - gray.r));
    g = Math.round(gray.g + intensity * (maxRed.g - gray.g));
    b = Math.round(gray.b + intensity * (maxRed.b - gray.b));
  } else {
    // Interpolieren von Grau zu MaxGrün je nach Abstand bis +30h
    const intensity = Math.min(totalHours / 30, 1);
    r = Math.round(gray.r + intensity * (maxGreen.r - gray.r));
    g = Math.round(gray.g + intensity * (maxGreen.g - gray.g));
    b = Math.round(gray.b + intensity * (maxGreen.b - gray.b));
  }

  const backgroundColor = `rgb(${r}, ${g}, ${b})`;
  card.style.backgroundColor = backgroundColor;
}


// Function to set progress bar for month card
function setMonthProgress() {
  const monthCard = document.getElementById('month-card');
  const currentHours = parseFloat(monthCard.getAttribute('data-current-hours'));
  const maxHours = parseFloat(monthCard.getAttribute('data-max-hours'));
  
  const progressBar = monthCard.querySelector('.progress-background');
  
  if (maxHours > 0) {
    const progressPercentage = Math.min((currentHours / maxHours) * 100, 100);
    progressBar.style.width = `${progressPercentage}%`;
  } else {
    progressBar.style.width = '0%';
  }
}

// Set the background color and progress when page loads
document.addEventListener('DOMContentLoaded', function() {
  setDynamicCardBackground();
  setMonthProgress();
});