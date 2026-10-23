const colors = {};

const accessibilityList = ["blind_friendly", "deaf_friendly", "pmr_friendly", "neurodiversity_friendly"];

const randomColors = [
    "#E8ADB6",
    "#CBADCC",
    "#A0ACC6",
    "#F75A3B",
    "#3F4EB5",
    "#8AC7AD",
    "#8AC7AD",
    "#9F63C4",
];

const getWeekNumber = (d) => {
    // https://stackoverflow.com/a/27125580
    // For 2024; no general solution....
    // UCLouvain weeksystem change every year impossible to have a general rule
    // Replace this by a dictionary?
    const onejan = new Date(d.getFullYear(), 0, 1);
    const dayOfYear = ((d - onejan + 86400000) / 86400000);
    const week = Math.ceil((dayOfYear + onejan.getDay() - 2) / 7);
    if (d.getFullYear() === 2024) {
        if (37 <= week && week <= 37 + 14) {
            return "S" + (week - 37).toString();
        }
        if (week <= 37 + 14 + 2) {
            return "Blocus";
        }
    }
    if (d.getFullYear() === 2025) {
        if ((2 <= week && week <= 4) || (5 + 13 + 2 + 2 < week && week <= 5 + 13 + 2 + 2 + 4)) {
            return "Examens";
        }
        if ((5 + 13 + 2 < week && week <= 5 + 13 + 2 + 2)) {
            return "Blocus";
        }
        if (week == 5 || (5 + 11 < week && week <= 5 + 11 + 2)) {
            return "Congé";
        }
        if (week <= 5 + 13 + 2) {
            const substract = week <= 5 + 11 ? 5 : 7;
            return "S" + (week - substract).toString();
        }
    }
    return "-";
}

function initPlaceColors() {
    for (place of places) {
        colors[place] = randomColors[Math.floor(Math.random() * randomColors.length)];
        const dot = document.getElementById("dot-" + place);
        dot.style.backgroundColor = colors[place];
    }
}

function isEventVisible(event) {
    const categoryElement = document.getElementById("checkbox-" + event.category.name);
    const placeElement = document.getElementById("checkbox-place-" + event.saved_location.name);
    let display = false;
    let atLeastOneChecked = false;
    for (accessibility of accessibilityList) {
        const accessibilityElement = document.getElementById("checkbox-" + accessibility);
        atLeastOneChecked |= accessibilityElement.checked;
        if (event[accessibility] && accessibilityElement.checked) {
            display = true;
        }
    }
    display |= !atLeastOneChecked;
    return display && categoryElement.checked && placeElement.checked;
}

function createCalendar() {
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: screen.width > 800 ? 'dayGridWeek' : 'dayGridDay',
        buttons: {
            addEvent: {
                text: 'Ajouter un événement',
                className: 'hide-on-mobile',
                click: function() {
                    location.href = "/add-event";
                }
            },
            today: { text: 'Aujourd\'hui' },
            dayGridDay: { text: 'Jour' },
            dayGridWeek: { text: 'Semaine', className: 'hide-on-mobile' },
            dayGridMonth: { text: 'Mois', className: 'hide-on-mobile' },
            listMonth: { text: 'Liste' },
        },
        locale: 'fr',
        firstDay: 1,
        headerToolbar: {
            start: 'addEvent',
            center: 'title',
            end: 'dayGridDay,dayGridWeek,dayGridMonth,listMonth prev,today,next',
        },
        headerToolbarClass: 'calendar-toolbar',
        toolbarSectionClass: function(arg) {
            return 'calendar-toolbar-' + arg.name;
        },
        views: {
            dayGridWeek: {
                dayHeaderFormat: { weekday: 'short', day: 'numeric', month: 'numeric' },
            },
        },
        navLinks: true,
        navLinkDayClick: 'dayGridDay',
        nextDayThreshold: '06:00:00',
        weekNumbers: true,
        inlineWeekNumberContent: function(arg) {
            return getWeekNumber(arg.date);
        },
        height: 'auto',
        titleFormat: { day: 'numeric', year: 'numeric', month: 'long' },
        eventTimeFormat: { hour: 'numeric', minute: '2-digit', hour12: false },
        eventDisplay: 'block',
        eventContrastColor: '#fff',
        eventSources : [
            {
                url: "/events",
            }
        ],
        // Filtering here rather than hiding elements, because FullCalendar 7 reuses
        // mounted event elements when the data hasn't changed
        eventSourceSuccess: function(rawEvents) {
            return rawEvents.filter(isEventVisible);
        },
        eventDataTransform: function(rawEvent) {
            rawEvent.color = colors[rawEvent.saved_location.name];
            return rawEvent;
        },
        eventClick: function(info) {
            location.href = "/event/" + info.event.id;
        },
        eventContent: function(arg) {
            if (arg.view.type === "listMonth") {
                return true;
            }
            const nodes = [];
            if (arg.timeText) {
                const time = document.createElement("div");
                time.className = "event-time";
                time.textContent = arg.timeText;
                nodes.push(time);
            }
            const title = document.createElement("div");
            title.className = "event-title";
            title.textContent = arg.event.title;
            nodes.push(title);
            if (screen.width > 900) {
                const locationEl = document.createElement("div");
                locationEl.textContent = "📍" + arg.event.extendedProps.location;
                nodes.push(locationEl);
            }
            const content = document.createElement("div");
            content.className = "event-content";
            content.append(...nodes);
            return { domNodes: [content] };
        },
    });
    calendar.render();
    for (category of categories) {
        document.getElementById("checkbox-" + category).addEventListener("change", function() {
            calendar.refetchEvents();
        });
    }
    for (place of places) {
        document.getElementById("checkbox-place-" + place).addEventListener("change", function() {
            calendar.refetchEvents();
        });
    }

    for (accessibility of accessibilityList) {
        document.getElementById("checkbox-" + accessibility).addEventListener("change", function() {
            calendar.refetchEvents();
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    initPlaceColors();
    createCalendar();
});