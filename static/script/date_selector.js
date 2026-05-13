// Date selector functionality
let selectedDate = null;

function formatDecimalComma(value) {
    const number = Number(value);

    if (Number.isNaN(number)) {
        return '';
    }

    if (Number.isInteger(number)) {
        return String(number);
    }

    return String(number).replace('.', ',');
}

function formatGermanDate(dateValue) {
    const date = new Date(`${dateValue}T00:00:00`);
    return date.toLocaleDateString('de-DE');
}

async function fetchHomeState({ method = 'GET', dateValue = null, formData = null } = {}) {
    const url = new URL(window.location.href);

    if (dateValue) {
        url.searchParams.set('date', dateValue);
    }

    const requestOptions = {
        method,
        headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'fetch'
        }
    };

    if (formData) {
        requestOptions.body = formData;
    }

    const response = await fetch(method === 'POST' ? window.location.pathname : url.toString(), requestOptions);

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Request failed');
    }

    return await response.json();
}

function renderOverviewData(overviewData) {
    const body = document.querySelector('#overviewModal .overview-body');

    if (!body || !overviewData) {
        return;
    }

    body.innerHTML = '';

    const years = Object.keys(overviewData).sort((a, b) => Number(b) - Number(a));

    years.forEach((yearKey) => {
        const yearContainer = document.createElement('div');
        yearContainer.className = 'overview-year';

        const yearHeading = document.createElement('h4');
        yearHeading.textContent = yearKey;
        yearContainer.appendChild(yearHeading);

        const months = Object.keys(overviewData[yearKey]).sort((a, b) => Number(b) - Number(a));

        months.forEach((monthKey) => {
            const monthData = overviewData[yearKey][monthKey];
            const monthContainer = document.createElement('div');
            monthContainer.className = 'overview-month';

            const monthHeader = document.createElement('div');
            monthHeader.className = 'month-header';

            const monthName = document.createElement('span');
            monthName.className = 'month-name';
            monthName.textContent = monthData.name;
            monthHeader.appendChild(monthName);

            if (monthData.difference !== null && monthData.difference !== undefined) {
                const differenceValue = Number(monthData.difference);
                const differenceSpan = document.createElement('span');
                differenceSpan.className = differenceValue > 0 ? 'month-surplus' : differenceValue < 0 ? 'month-deficit' : 'month-neutral';
                differenceSpan.textContent = differenceValue > 0 ? `+${formatDecimalComma(differenceValue)}h` : differenceValue < 0 ? `${formatDecimalComma(differenceValue)}h` : '0h';
                monthHeader.appendChild(differenceSpan);
            }

            monthContainer.appendChild(monthHeader);

            (monthData.entries || []).forEach((entry) => {
                const entryRow = document.createElement('div');
                entryRow.className = 'overview-entry';

                const entryDate = document.createElement('span');
                entryDate.className = 'entry-date';
                entryDate.textContent = formatGermanDate(entry.date);

                const entryHours = document.createElement('span');
                entryHours.className = 'entry-hours';
                entryHours.textContent = `${formatDecimalComma(entry.hours)}h`;

                entryRow.appendChild(entryDate);
                entryRow.appendChild(entryHours);
                monthContainer.appendChild(entryRow);
            });

            yearContainer.appendChild(monthContainer);
        });

        body.appendChild(yearContainer);
    });
}

function applyHomeState(state) {
    if (!state) {
        return;
    }

    const datePicker = document.getElementById('date-picker');
    if (datePicker && state.selected_date) {
        datePicker.value = state.selected_date;
        selectedDate = state.selected_date;
    }

    if (state.selected_date) {
        localStorage.setItem('selectedDate', state.selected_date);

        const currentUrl = new URL(window.location.href);
        currentUrl.searchParams.set('date', state.selected_date);
        window.history.replaceState({}, '', currentUrl.toString());
    }

    document.querySelectorAll('input[name="selected_date"]').forEach((input) => {
        if (state.selected_date) {
            input.value = state.selected_date;
        }
    });

    const totalCard = document.getElementById('total-hours-card');
    if (totalCard) {
        totalCard.setAttribute('data-hours', state.total_hours_numeric ?? 0);
        const totalValue = totalCard.querySelector('.card-value');
        if (totalValue && state.total_hours !== undefined) {
            totalValue.textContent = `${state.total_hours}h`;
        }
    }

    const monthCard = document.getElementById('month-card');
    if (monthCard) {
        monthCard.setAttribute('data-current-hours', state.month_hours_numeric ?? 0);
        monthCard.setAttribute('data-max-hours', state.current_max_hours_numeric ?? 0);

        const monthTitle = monthCard.querySelector('.card-title');
        if (monthTitle && state.selected_month_name) {
            monthTitle.textContent = state.selected_month_name;
        }

        const monthValue = monthCard.querySelector('.card-value');
        if (monthValue && state.month_hours !== undefined) {
            monthValue.textContent = `${state.month_hours}h`;
        }
    }

    const editTimeDisplay = document.getElementById('edit-time-display');
    if (editTimeDisplay && state.edit_time) {
        editTimeDisplay.textContent = state.edit_time;
    }

    const timePicker = document.getElementById('time-picker');
    if (timePicker && state.edit_time_24h) {
        timePicker.value = state.edit_time_24h;
    }

    const maxHoursInput = document.getElementById('maxHoursInput');
    if (maxHoursInput) {
        maxHoursInput.placeholder = `${state.suggested_max_hours_display || ''}h`;
    }

    renderOverviewData(state.overview_data);

    if (typeof setDynamicCardBackground === 'function') {
        setDynamicCardBackground();
    }

    if (typeof setMonthProgress === 'function') {
        setMonthProgress();
    }

    formatDateInput();
}

function selectDate(dateValue) {
    if (!dateValue) return;
    
    selectedDate = dateValue;
    
    // Store selected date and refresh the page state without a full reload
    updateSelectedDate(dateValue);
}

async function updateSelectedDate(dateValue) {
    localStorage.setItem('selectedDate', dateValue);

    try {
        const state = await fetchHomeState({ method: 'GET', dateValue });
        applyHomeState(state);
    } catch (error) {
        console.error('Could not update selected date without reload:', error);
        const currentUrl = new URL(window.location.href);
        currentUrl.searchParams.set('date', dateValue);
        window.location.href = currentUrl.toString();
    }
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
    const datePicker = document.getElementById('date-picker');
    
    if (!datePicker) {
        return;
    }
    
    // Use the value provided by the server
    if (datePicker.value) {
        selectedDate = datePicker.value;
    } else {
        // Fallback to today if no value is set
        const today = new Date().toISOString().split('T')[0];
        datePicker.value = today;
        selectedDate = today;
    }
    
    // Format the date input on load
    formatDateInput();
    
    // Add event listener for async home actions
    document.querySelectorAll('form[data-home-action]').forEach((form) => {
        form.addEventListener('submit', async function(event) {
            event.preventDefault();

            try {
                const state = await fetchHomeState({
                    method: 'POST',
                    formData: new FormData(form)
                });

                applyHomeState(state);

                if (form.dataset.homeAction === 'set_max_hours') {
                    closeMaxHoursModal();
                }
            } catch (error) {
                console.error('Home action failed without reload:', error);
                form.submit();
            }
        });
    });

    datePicker.addEventListener('change', function() {
        selectDate(this.value);
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

    const formData = new FormData();
    formData.append('action', 'set_time');
    formData.append('selected_date', selectedDate);
    formData.append('time_value', roundedTime);

    fetchHomeState({
        method: 'POST',
        formData
    })
        .then((state) => {
            applyHomeState(state);
            closeTimeInput();
        })
        .catch((error) => {
            console.error('Time update failed without reload:', error);
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
        });
}

// Add both click and touch event listeners for modal closing
window.addEventListener('click', handleModalClose);
window.addEventListener('touchend', handleModalClose);