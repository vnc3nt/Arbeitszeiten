// Date selector functionality
let selectedDate = null;

function selectDate(dateValue) {
    console.log('selectDate called with:', dateValue); // Debug
    
    if (!dateValue) return;
    
    selectedDate = dateValue;
    const displayElement = document.getElementById('selected-date-display');
    
    if (displayElement) {
        const selectedDateObj = new Date(dateValue);
        const today = new Date();
        
        // Normalize dates to compare only date part (not time)
        const isToday = selectedDateObj.toDateString() === today.toDateString();
        
        if (isToday) {
            displayElement.textContent = 'Heute';
        } else {
            // Format date in German format (DD.MM.YYYY)
            const formattedDate = selectedDateObj.toLocaleDateString('de-DE', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
            displayElement.textContent = formattedDate;
        }
    }
    
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

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Date selector initialized'); // Debug
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
    
    // Make the day-selection clickable to focus the date input
    const daySelection = document.getElementById('day-selection');
    if (daySelection) {
        daySelection.addEventListener('click', function(e) {
            // Don't trigger if clicking on the date input itself
            if (e.target.id !== 'date-picker') {
                datePicker.focus();
                try {
                    datePicker.showPicker();
                } catch (err) {
                    // showPicker not supported in all browsers
                    console.log('showPicker not supported');
                }
            }
        });
    }
});