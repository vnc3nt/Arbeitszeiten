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