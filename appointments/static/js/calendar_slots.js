const daysContainer = document.getElementById('calendar-days');
const slotsContainer = document.getElementById('available-slots');
const prevButton = document.getElementById('prev-week-btn');
const nextButton = document.getElementById('next-week-btn');

const today = new Date(); // Current day
const twoWeeksLater = new Date();
twoWeeksLater.setDate(today.getDate() + 13); // Limit to next 14 days
let currentStartDate = new Date(today); // Start date for visible calendar days
let visibleDays = 7; // Show 7 days at a time
let slots = {}; // Slots will be populated dynamically


// Extract doctor username from the URLconst today = new Date(); // Current day

function getDoctorUsernameFromUrl() {
    // Assuming the URL structure is /view_doctor_profile_by_cli/<doctor_username>/
    const pathParts = window.location.pathname.split('/');
    // The username is the last part of the URL after "view_doctor_profile_by_cli"
    return pathParts[pathParts.length - 2]; // Get the second-to-last part
}


// Fetch slots dynamically from the backend
function fetchSlots() {
    const doctorUsername = getDoctorUsernameFromUrl(); // Get the doctor username from the URL

    fetch(`/view_doctor_profile_by_cli/${doctorUsername}/fetch_slots/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.status === 'success') {
                slots = data.slots; // Update slots object dynamically
                renderDays(); // Render calendar days
                renderSlots(new Date()); // Render slots for today
            } else {
                console.error('Error fetching slots:', data.message);
            }
        })
        .catch((error) => {
            console.error('Error fetching slots:', error);
        });
}

// Function to render the calendar days
function renderDays() {
    daysContainer.innerHTML = ''; // Clear existing days

    for (let i = 0; i < visibleDays; i++) {
        const date = new Date(currentStartDate);
        date.setDate(currentStartDate.getDate() + i);

        // Stop rendering days beyond the limit
        if (date > twoWeeksLater) break;

        const dayElement = document.createElement('div');
        dayElement.style.textAlign = 'center';
        dayElement.style.flex = '1';
        dayElement.style.cursor = 'pointer';

        const isToday = today.toDateString() === date.toDateString();
        dayElement.innerHTML = `
            <p style="margin: 0; font-weight: ${isToday ? 'bold' : 'normal'}; color: ${
            isToday ? '#007bff' : '#000'
        };">${date.toLocaleDateString('en-US', { weekday: 'short' })}</p>
            <p style="margin: 0; font-size: 14px; color: ${
            isToday ? '#007bff' : '#555'
        };">${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</p>
        `;

        dayElement.addEventListener('click', () => renderSlots(date));
        daysContainer.appendChild(dayElement);
    }

    // Enable or disable navigation buttons
    prevButton.disabled = currentStartDate <= today;
    nextButton.disabled =
        currentStartDate > twoWeeksLater ||
        currentStartDate.getDate() + visibleDays > twoWeeksLater.getDate();
}

// Function to render slots for a selected date
function renderSlots(selectedDate) {
    slotsContainer.innerHTML = ''; // Clear existing slots
    const dateKey = selectedDate.toISOString().split('T')[0]; // Format date as YYYY-MM-DD
    const availableSlots = slots[dateKey] || [];

    if (availableSlots.length === 0) {
        slotsContainer.innerHTML = '<p style="color: #999;">No Slots Available</p>';
        return;
    }

    availableSlots.forEach((slot) => {
        const slotElement = document.createElement('button');
        slotElement.textContent = `${slot.start_time} - ${slot.end_time}`;
        slotElement.style.cssText =
            'padding: 10px 15px; border: 1px solid #007bff; border-radius: 5px; background-color: white; color: #007bff; cursor: pointer;';
        slotsContainer.appendChild(slotElement);
    });
}

// Function to navigate weeks
function navigateDays(step) {
    currentStartDate.setDate(currentStartDate.getDate() + step);
    renderDays();
}

// Initial fetch and render
fetchSlots(); // Fetch slots when the page loads