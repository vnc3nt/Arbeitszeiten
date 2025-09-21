// Date selector functionality
let selectedDate = null;

function selectDate(dateValue) {
    console.log('selectDate called with:', dateValue);
    
    if (!dateValue) return;
    
    selectedDate = dateValue;
    
    // Store selected date and reload page
    updateSelectedDate(dateValue);
}

function updateSelectedDate(dateValue) {
    // Store the selected date and reload the page with the new date
    localStorage.setItem('selectedDate', dateValue);
    
    // Reload the page with the new date parameter
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('date', dateValue);
    window.location.href = currentUrl.toString();
}

function formatDateInput() {
    const datePicker = document.getElementById('date-picker');
    if (!datePicker || !datePicker.value) return;
    
    const selectedDateObj = new Date(datePicker.value);
    const today = new Date();
    
    // Check if the selected date is today
    const isToday = selectedDateObj.toDateString() === today.toDateString();
    
    if (isToday) {
        // Create a custom display for "today"
        datePicker.style.color = 'transparent';
        const displaySpan = document.createElement('span');
        displaySpan.textContent = 'Heute';
        displaySpan.style.position = 'absolute';
        displaySpan.style.top = '50%';
        displaySpan.style.left = '50%';
        displaySpan.style.transform = 'translate(-50%, -50%)';
        displaySpan.style.pointerEvents = 'none';
        displaySpan.style.color = 'inherit';
        displaySpan.id = 'today-label';
        
        // Remove existing label if any
        const existingLabel = document.getElementById('today-label');
        if (existingLabel) {
            existingLabel.remove();
        }
        
        datePicker.parentElement.appendChild(displaySpan);
    } else {
        // Remove "today" label if it exists
        const existingLabel = document.getElementById('today-label');
        if (existingLabel) {
            existingLabel.remove();
        }
        datePicker.style.color = 'inherit';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Date selector initialized');
    const datePicker = document.getElementById('date-picker');
    
    if (!datePicker) {
        console.error('Date picker element not found during initialization');
        return;
    }
    
    // Use the value provided by the server
    if (datePicker.value) {
        selectedDate = datePicker.value;
        console.log('Initial selected date from server:', selectedDate);
    } else {
        // Fallback to today if no value is set
        const today = new Date().toISOString().split('T')[0];
        datePicker.value = today;
        selectedDate = today;
        console.log('Set default date to today:', selectedDate);
    }
    
    // Format the date input on load
    formatDateInput();
    
    // Add event listener for when the date changes
    datePicker.addEventListener('change', function() {
        formatDateInput();
    });
});

// MaxHours Modal functions
function openMaxHoursModal() {
    const modal = document.getElementById('maxHoursModal');
    const input = document.getElementById('maxHoursInput');
    
    if (modal && input) {
        modal.style.display = 'block';
        input.focus();
    }
}

function closeMaxHoursModal() {
    const modal = document.getElementById('maxHoursModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function openOverviewModal() {
    const modal = document.getElementById('overviewModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeOverviewModal() {
    const modal = document.getElementById('overviewModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Close modal when clicking or touching outside
function handleModalClose(event) {
    const maxHoursModal = document.getElementById('maxHoursModal');
    const overviewModal = document.getElementById('overviewModal');
    
    if (maxHoursModal && event.target === maxHoursModal) {
        closeMaxHoursModal();
    }
    
    if (overviewModal && event.target === overviewModal) {
        closeOverviewModal();
    }
}

// Time input functions
function openTimeInput() {
    const timeDisplay = document.getElementById('edit-time-display');
    const timePicker = document.getElementById('time-picker');
    
    if (timeDisplay && timePicker) {
        timeDisplay.style.display = 'none';
        timePicker.style.display = 'inline-block';
        timePicker.focus();
        
        // Add blur event listener to hide when clicking outside
        timePicker.addEventListener('blur', function() {
            closeTimeInput();
        });
    }
}

function closeTimeInput() {
    const timeDisplay = document.getElementById('edit-time-display');
    const timePicker = document.getElementById('time-picker');
    
    if (timeDisplay && timePicker) {
        timeDisplay.style.display = 'inline-block';
        timePicker.style.display = 'none';
    }
}

function updateTime(timeValue) {
    if (!timeValue) return;
    
    // Round time to nearest 15 minutes
    function roundToQuarterHour(timeStr) {
        const [hours, minutes] = timeStr.split(':').map(Number);
        const totalMinutes = hours * 60 + minutes;
        const roundedMinutes = Math.round(totalMinutes / 15) * 15;
        const roundedHours = Math.floor(roundedMinutes / 60);
        const remainingMinutes = roundedMinutes % 60;
        return `${String(roundedHours).padStart(2, '0')}:${String(remainingMinutes).padStart(2, '0')}`;
    }
    
    const roundedTime = roundToQuarterHour(timeValue);
    const selectedDate = document.getElementById('date-picker').value;
    
    // Send time update to server
    const form = document.createElement('form');
    form.method = 'POST';
    form.style.display = 'none';
    
    const actionInput = document.createElement('input');
    actionInput.type = 'hidden';
    actionInput.name = 'action';
    actionInput.value = 'set_time';
    form.appendChild(actionInput);
    
    const dateInput = document.createElement('input');
    dateInput.type = 'hidden';
    dateInput.name = 'selected_date';
    dateInput.value = selectedDate;
    form.appendChild(dateInput);
    
    const timeInput = document.createElement('input');
    timeInput.type = 'hidden';
    timeInput.name = 'time_value';
    timeInput.value = roundedTime;
    form.appendChild(timeInput);
    
    document.body.appendChild(form);
    form.submit();
}

// Add both click and touch event listeners for modal closing
window.addEventListener('click', handleModalClose);
window.addEventListener('touchend', handleModalClose);