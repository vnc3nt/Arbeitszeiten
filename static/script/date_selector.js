// Date selector functionality
let selectedDate = null;
const overviewCache = new Map();
let activeActionRequests = 0;
let actionErrorTimer = null;
let latestHomeMutationId = 0;
const numberAnimationTokens = new WeakMap();
const timeAnimationTokens = new WeakMap();

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

function formatDecimalCommaLimited(value, maxDecimals = 2) {
    const number = Number(value);

    if (Number.isNaN(number)) {
        return '';
    }

    // Round to specified decimal places
    const rounded = Math.round(number * Math.pow(10, maxDecimals)) / Math.pow(10, maxDecimals);

    if (Math.floor(rounded) === rounded) {
        return String(Math.floor(rounded));
    }

    return String(rounded).replace('.', ',');
}

function formatHoursWithStableWidth(value) {
    const number = Number(value);
    if (Number.isNaN(number)) return '';

    // Immer strikt auf 2 Nachkommastellen runden
    const rounded = Math.round(number * 100) / 100;
    const isInteger = Math.floor(rounded) === rounded;

    // Festes Format erzeugen (z.B. "10.00" oder "10.50")
    const fixedString = rounded.toFixed(2);
    const parts = fixedString.split('.');
    const intPart = parts[0];
    const decPart = parts[1];

    if (isInteger) {
        // Bei ganzen Zahlen: Komma und Nachkommastellen unsichtbar machen (reserviert aber den Platz!)
        return `${intPart}<span style="visibility: hidden;" aria-hidden="true">,${decPart}</span>h`;
    } else {
        // Bei Kommazahlen: Normal anzeigen
        return `${intPart},${decPart}h`;
    }
}

function formatGermanDate(dateValue) {
    const date = new Date(`${dateValue}T00:00:00`);
    return date.toLocaleDateString('de-DE');
}

function parseLocaleNumber(value) {
    if (value === null || value === undefined || value === '') {
        return 0;
    }

    const normalized = String(value).replace('h', '').replace(',', '.');
    const number = Number.parseFloat(normalized);
    return Number.isNaN(number) ? 0 : number;
}

function formatTimeDisplay(decimalHours) {
    if (decimalHours === 0) {
        return '0:00';
    }

    const hours = Math.trunc(decimalHours);
    const minutes = Math.round((decimalHours - hours) * 60);
    return `${hours}:${String(minutes).padStart(2, '0')}`;
}

function formatTimeInputValue(decimalHours) {
    if (decimalHours === 0) {
        return '00:00';
    }

    const hours = Math.trunc(decimalHours);
    const minutes = Math.round((decimalHours - hours) * 60);
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
}

function parseClockToDecimal(clockValue) {
    if (!clockValue || !clockValue.includes(':')) {
        return 0;
    }

    const [hoursText, minutesText] = clockValue.split(':');
    const hours = Number.parseInt(hoursText, 10);
    const minutes = Number.parseInt(minutesText, 10);

    if (Number.isNaN(hours) || Number.isNaN(minutes)) {
        return 0;
    }

    return hours + (minutes / 60);
}

// Easing function for smooth animation
function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
}

// Animate number change with smooth counter animation
function animateNumberChange(element, startValue, endValue, duration = 400) {
    if (!element || startValue === endValue) {
        return;
    }

    const animationToken = (numberAnimationTokens.get(element) || 0) + 1;
    numberAnimationTokens.set(element, animationToken);

    const difference = endValue - startValue;
    const startTime = performance.now();

    function update(currentTime) {
        if (numberAnimationTokens.get(element) !== animationToken) {
            return;
        }

        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = easeOutCubic(progress);
        const currentValue = startValue + difference * easeProgress;

        // GEÄNDERT: Nutze innerHTML und unsere neue "Stable Width" Funktion
        element.innerHTML = formatHoursWithStableWidth(currentValue);

        // Continue animation if not finished
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            // Ensure final value is exact
            if (numberAnimationTokens.get(element) === animationToken) {
                // GEÄNDERT: Auch hier innerHTML nutzen
                element.innerHTML = formatHoursWithStableWidth(endValue);
            }
        }
    }

    requestAnimationFrame(update);
}

// Animate time display (format: H:MM)
function animateTimeDisplay(element, startDecimal, endDecimal, duration = 400) {
    if (!element || startDecimal === endDecimal) {
        return;
    }

    const animationToken = (timeAnimationTokens.get(element) || 0) + 1;
    timeAnimationTokens.set(element, animationToken);

    const difference = endDecimal - startDecimal;
    const startTime = performance.now();

    function update(currentTime) {
        if (timeAnimationTokens.get(element) !== animationToken) {
            return;
        }

        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = easeOutCubic(progress);
        const currentValue = startDecimal + difference * easeProgress;

        // Format and display the current value
        element.textContent = formatTimeDisplay(currentValue);

        // Continue animation if not finished
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            // Ensure final value is exact
            if (timeAnimationTokens.get(element) === animationToken) {
                element.textContent = formatTimeDisplay(endDecimal);
            }
        }
    }

    requestAnimationFrame(update);
}

function getSelectedDateValue() {
    const datePicker = document.getElementById('date-picker');
    return datePicker ? datePicker.value : selectedDate;
}

function getLoadingOverlay() {
    return document.getElementById('action-loading-indicator');
}

function getErrorBanner() {
    return document.getElementById('action-error-banner');
}

function showActionLoading() {
    activeActionRequests += 1;

    const indicator = getLoadingOverlay();
    if (indicator) {
        indicator.style.display = 'block';
        indicator.setAttribute('aria-hidden', 'false');
    }
}

function hideActionLoading() {
    activeActionRequests = Math.max(0, activeActionRequests - 1);

    if (activeActionRequests > 0) {
        return;
    }

    const indicator = getLoadingOverlay();
    if (indicator) {
        indicator.style.display = 'none';
        indicator.setAttribute('aria-hidden', 'true');
    }
}

function showActionError(message) {
    const banner = getErrorBanner();
    if (!banner) {
        return;
    }

    if (actionErrorTimer) {
        window.clearTimeout(actionErrorTimer);
    }

    banner.textContent = message;
    banner.classList.add('is-visible');
    banner.style.display = 'block';

    actionErrorTimer = window.setTimeout(() => {
        banner.classList.remove('is-visible');
        banner.style.display = 'none';
    }, 4200);
}

function captureHomeSnapshot() {
    const totalCard = document.getElementById('total-hours-card');
    const monthCard = document.getElementById('month-card');
    const editTimeDisplay = document.getElementById('edit-time-display');
    const timePicker = document.getElementById('time-picker');
    const maxHoursInput = document.getElementById('maxHoursInput');

    return {
        totalHoursText: totalCard?.querySelector('.card-value')?.innerHTML ?? '',
        totalHoursData: totalCard?.getAttribute('data-hours') ?? '0',
        monthHoursText: monthCard?.querySelector('.card-value')?.innerHTML ?? '',
        monthHoursData: monthCard?.getAttribute('data-current-hours') ?? '0',
        monthMaxHoursData: monthCard?.getAttribute('data-max-hours') ?? '0',
        editTimeText: editTimeDisplay?.textContent ?? '',
        timePickerValue: timePicker?.value ?? '',
        maxHoursPlaceholder: maxHoursInput?.placeholder ?? ''
    };
}

function restoreHomeSnapshot(snapshot) {
    if (!snapshot) {
        return;
    }

    const totalCard = document.getElementById('total-hours-card');
    const monthCard = document.getElementById('month-card');
    const editTimeDisplay = document.getElementById('edit-time-display');
    const timePicker = document.getElementById('time-picker');
    const maxHoursInput = document.getElementById('maxHoursInput');

    if (totalCard) {
        totalCard.setAttribute('data-hours', snapshot.totalHoursData);
        const totalValue = totalCard.querySelector('.card-value');
        if (totalValue) {
            totalValue.innerHTML = snapshot.totalHoursText;
        }
    }

    if (monthCard) {
        monthCard.setAttribute('data-current-hours', snapshot.monthHoursData);
        monthCard.setAttribute('data-max-hours', snapshot.monthMaxHoursData);
        const monthValue = monthCard.querySelector('.card-value');
        if (monthValue) {
            monthValue.innerHTML = snapshot.monthHoursText;
        }
    }

    if (editTimeDisplay) {
        editTimeDisplay.textContent = snapshot.editTimeText;
    }

    if (timePicker) {
        timePicker.value = snapshot.timePickerValue;
    }

    if (maxHoursInput) {
        maxHoursInput.placeholder = snapshot.maxHoursPlaceholder;
    }

    if (typeof setDynamicCardBackground === 'function') {
        setDynamicCardBackground();
    }

    if (typeof setMonthProgress === 'function') {
        setMonthProgress();
    }
}

function updateNumericCard(cardId, delta, selector) {
    const card = document.getElementById(cardId);
    if (!card || !Number.isFinite(delta) || delta === 0) {
        return;
    }

    const currentValue = parseLocaleNumber(card.getAttribute('data-hours') || card.getAttribute('data-current-hours'));
    const newValue = currentValue + delta;
    const valueElement = selector ? card.querySelector(selector) : card.querySelector('.card-value');

    if (valueElement) {
        animateNumberChange(valueElement, currentValue, newValue, 400);
    }

    if (card.id === 'total-hours-card') {
        card.setAttribute('data-hours', String(newValue));
    } else {
        card.setAttribute('data-current-hours', String(newValue));
    }
}

function startHomeMutation() {
    latestHomeMutationId += 1;
    return latestHomeMutationId;
}

function isLatestHomeMutation(mutationId) {
    return mutationId === latestHomeMutationId;
}

function updateEditTimeDisplay(decimalHours) {
    const editTimeDisplay = document.getElementById('edit-time-display');
    const timePicker = document.getElementById('time-picker');

    if (editTimeDisplay) {
        const currentTime = parseClockToDecimal(editTimeDisplay.textContent);
        animateTimeDisplay(editTimeDisplay, currentTime, decimalHours, 400);
    }

    if (timePicker) {
        timePicker.value = formatTimeInputValue(decimalHours);
    }
}

function applyOptimisticHomeAction(form) {
    const action = form.dataset.homeAction;

    if (action === 'add_30' || action === 'sub_30') {
        const currentTime = parseClockToDecimal(document.getElementById('edit-time-display')?.textContent);
        const requestedDelta = action === 'add_30' ? 0.5 : -0.5;
        const nextTime = Math.max(0, currentTime + requestedDelta);
        const appliedDelta = nextTime - currentTime;

        updateNumericCard('month-card', appliedDelta, '.card-value');
        updateNumericCard('total-hours-card', appliedDelta, '.card-value');
        updateEditTimeDisplay(nextTime);
    }
}

async function fetchHomeState({ method = 'GET', dateValue = null, formData = null, includeOverview = false } = {}) {
    const url = new URL(window.location.href);

    if (dateValue) {
        url.searchParams.set('date', dateValue);
    }

    if (includeOverview) {
        url.searchParams.set('include_overview', '1');
    }

    showActionLoading();

    try {
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
    } finally {
        hideActionLoading();
    }
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

// NEU: snapshot = null als zweiter Parameter hinzugefügt
function applyHomeState(state, snapshot = null) {
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
        // GEÄNDERT: domTotal = aktueller Wert, baseTotal = Wert VOR dem Klick
        const domTotal = parseLocaleNumber(totalCard.getAttribute('data-hours'));
        const baseTotal = snapshot ? parseLocaleNumber(snapshot.totalHoursData) : domTotal;
        
        const nextTotal = state.total_hours_numeric !== undefined
            ? Number(state.total_hours_numeric)
            : baseTotal + (state.total_hours_delta !== undefined ? Number(state.total_hours_delta) : 0);
            
        totalCard.setAttribute('data-hours', String(nextTotal));
        const totalValue = totalCard.querySelector('.card-value');
        if (totalValue) {
            if (state.total_hours !== undefined || state.total_hours_delta !== undefined) {
                // GEÄNDERT: Animation startet vom aktuellen DOM-Wert zum neuen echten Wert
                animateNumberChange(totalValue, domTotal, nextTotal, 400);
            }
        }
    }

    const monthCard = document.getElementById('month-card');
    if (monthCard) {
        // GEÄNDERT: domMonth = aktueller Wert, baseMonth = Wert VOR dem Klick
        const domMonth = parseLocaleNumber(monthCard.getAttribute('data-current-hours'));
        const baseMonth = snapshot ? parseLocaleNumber(snapshot.monthHoursData) : domMonth;
        
        const nextMonth = state.month_hours_numeric !== undefined
            ? Number(state.month_hours_numeric)
            : baseMonth + (state.month_hours_delta !== undefined ? Number(state.month_hours_delta) : 0);
            
        monthCard.setAttribute('data-current-hours', String(nextMonth));

        if (state.current_max_hours_numeric !== undefined) {
            monthCard.setAttribute('data-max-hours', String(state.current_max_hours_numeric));
        }

        const monthTitle = monthCard.querySelector('.card-title');
        if (monthTitle && state.selected_month_name) {
            monthTitle.textContent = state.selected_month_name;
        }

        const monthValue = monthCard.querySelector('.card-value');
        if (monthValue) {
            if (state.month_hours !== undefined || state.month_hours_delta !== undefined) {
                // GEÄNDERT: Animation startet vom aktuellen DOM-Wert zum neuen echten Wert
                animateNumberChange(monthValue, domMonth, nextMonth, 400);
            }
        }
    }

    const editTimeDisplay = document.getElementById('edit-time-display');
    if (editTimeDisplay && state.edit_time) {
        const currentTime = parseClockToDecimal(editTimeDisplay.textContent);
        const nextTime = parseClockToDecimal(state.edit_time);
        if (currentTime !== nextTime) {
            animateTimeDisplay(editTimeDisplay, currentTime, nextTime, 400);
        } else {
            editTimeDisplay.textContent = state.edit_time;
        }
    }

    const timePicker = document.getElementById('time-picker');
    if (timePicker && state.edit_time_24h) {
        timePicker.value = state.edit_time_24h;
    }

    const maxHoursInput = document.getElementById('maxHoursInput');
    if (maxHoursInput) {
        maxHoursInput.placeholder = `${state.suggested_max_hours_display || ''}h`;
    }

    if (state.data_changed) {
        overviewCache.delete(state.selected_date || getSelectedDateValue());
    }

    if (state.overview_data) {
        renderOverviewData(state.overview_data);
        overviewCache.set(state.selected_date || getSelectedDateValue(), state.overview_data);
    }

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
        const state = await fetchHomeState({ method: 'GET', dateValue, includeOverview: false });
        applyHomeState(state);
    } catch (error) {
        showActionError('Datum konnte nicht aktualisiert werden. Bitte erneut versuchen.');
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

            const mutationId = startHomeMutation();
            const snapshot = captureHomeSnapshot();
            applyOptimisticHomeAction(form);

            try {
                const state = await fetchHomeState({
                    method: 'POST',
                    formData: new FormData(form)
                });

                if (!isLatestHomeMutation(mutationId)) {
                    return;
                }

                applyHomeState(state, snapshot);

                if (form.dataset.homeAction === 'set_max_hours') {
                    closeMaxHoursModal();
                }
            } catch (error) {
                if (!isLatestHomeMutation(mutationId)) {
                    return;
                }

                restoreHomeSnapshot(snapshot);
                showActionError('Änderung konnte nicht gespeichert werden. Bitte erneut versuchen.');
                console.error('Home action failed without reload:', error);
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

        const currentDate = getSelectedDateValue();
        const cachedOverview = overviewCache.get(currentDate);

        if (cachedOverview) {
            renderOverviewData(cachedOverview);
            return;
        }

        const body = modal.querySelector('.overview-body');
        if (body) {
            body.innerHTML = `
                <div class="overview-skeletons" aria-hidden="true">
                    <span class="sr-only">Inhalte werden geladen</span>
                    ${Array.from({ length: 6 }).map(() => `
                        <div class="skeleton-row">
                            <div class="skeleton-thumb"></div>
                            <div class="skeleton-lines">
                                <div class="skeleton-line short"></div>
                                <div class="skeleton-line long"></div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            // mark modal as busy for accessibility
            modal.setAttribute('aria-busy', 'true');
        }

        fetchHomeState({ method: 'GET', dateValue: currentDate, includeOverview: true })
            .then((state) => {
                if (state.overview_data) {
                    overviewCache.set(currentDate, state.overview_data);
                    renderOverviewData(state.overview_data);
                    // loading finished
                    modal.removeAttribute('aria-busy');
                }
            })
            .catch((error) => {
                const body = modal.querySelector('.overview-body');
                if (body) {
                    body.innerHTML = '<div class="overview-loading-container"><div class="overview-loading-text">Übersicht konnte nicht geladen werden.</div></div>';
                }
                modal.removeAttribute('aria-busy');
                showActionError('Übersicht konnte nicht geladen werden. Bitte erneut versuchen.');
                console.error('Overview loading failed:', error);
            });
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
let pendingTimeInputValue = null;

function openTimeInput() {
    const timeDisplay = document.getElementById('edit-time-display');
    const timePickerContainer = document.getElementById('time-picker-container');
    const timePicker = document.getElementById('time-picker');
    
    if (timeDisplay && timePickerContainer && timePicker) {
        timeDisplay.style.display = 'none';
        timePickerContainer.style.display = 'inline-flex';
        timePicker.focus();
    }
}

function closeTimeInput() {
    const timeDisplay = document.getElementById('edit-time-display');
    const timePickerContainer = document.getElementById('time-picker-container');
    
    if (timeDisplay && timePickerContainer) {
        timeDisplay.style.display = 'inline-block';
        timePickerContainer.style.display = 'none';
    }
}

function confirmTimeInput() {
    const timePicker = document.getElementById('time-picker');
    const timeValue = pendingTimeInputValue || timePicker?.value;

    if (timeValue) {
        pendingTimeInputValue = null;
        updateTime(timeValue);
    }
}

function cancelTimeInput() {
    pendingTimeInputValue = null;
    closeTimeInput();
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
    const currentDayTime = parseClockToDecimal(document.getElementById('edit-time-display')?.textContent);
    const nextDayTime = parseClockToDecimal(roundedTime);
    const timeDelta = nextDayTime - currentDayTime;
    const snapshot = captureHomeSnapshot();
    const mutationId = startHomeMutation();

    const formData = new FormData();
    formData.append('action', 'set_time');
    formData.append('selected_date', selectedDate);
    formData.append('time_value', roundedTime);

    updateEditTimeDisplay(nextDayTime);
    updateNumericCard('month-card', timeDelta, '.card-value');
    updateNumericCard('total-hours-card', timeDelta, '.card-value');

    fetchHomeState({
        method: 'POST',
        formData
    })
        .then((state) => {
            if (!isLatestHomeMutation(mutationId)) {
                return;
            }

            applyHomeState(state, snapshot);
            closeTimeInput();
        })
        .catch((error) => {
            if (!isLatestHomeMutation(mutationId)) {
                return;
            }

            restoreHomeSnapshot(snapshot);
            showActionError('Zeit konnte nicht gespeichert werden. Bitte erneut versuchen.');
            console.error('Time update failed without reload:', error);
        });
}

// Initialize time picker buttons
document.addEventListener('DOMContentLoaded', function() {
    const timePicker = document.getElementById('time-picker');
    if (timePicker) {
        timePicker.addEventListener('change', function() {
            if (timePicker.value) {
                pendingTimeInputValue = timePicker.value;
            }
        });

        timePicker.addEventListener('blur', function() {
            if (pendingTimeInputValue) {
                confirmTimeInput();
            }
        });
    }
});

// Add both click and touch event listeners for modal closing
window.addEventListener('click', handleModalClose);
window.addEventListener('touchend', handleModalClose);