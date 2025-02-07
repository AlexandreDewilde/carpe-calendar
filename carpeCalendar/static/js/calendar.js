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

function createCalendar() {
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        themeSystem: 'bootstrap5',
        initialView: screen.width > 800 ? 'dayGridWeek' : 'dayGridDay',
        customButtons: {
            addEvent: {
                text: 'Ajouter un événement',
                click: function() {
                    location.href = "/add-event";
                }
            },
            today: {
                text: 'Aujourd\'hui',
                click: function() {
                    calendar.today();
                }
            }
        },
        locale: 'fr',
        firstDay: 1,
        headerToolbar: {
            left: 'addEvent',
            center: 'title',
            right: 'dayGridDay,dayGridWeek,dayGridMonth,listMonth prev,today,next',
        },
        buttonText: {
            month: 'Mois',
            listMonth: "Liste",
            week: 'Semaine',
            day: 'Jour',
            today: 'Aujourd\'hui',

        },
        navLinks: true,
        nextDayThreshold: '06:00:00',
        weekNumbers: true,
        weekNumberContent: function(obj) {
            return getWeekNumber(obj.date);
        },
        navLinkDayClick: function(date) {
            calendar.changeView('dayGridDay', date.toISOString());
        },
        height: 'auto',
        eventBorderColor: 'black',
        titleFormat: { day: 'numeric', year: 'numeric', month: 'long' },
        eventTimeFormat: { hour: 'numeric', minute: '2-digit', hour12: false },
        eventDisplay: 'block',
        eventBorderColor: 'gray',
        eventSources : [
            {
                url: "/events",
            }
        ],
        eventClick: function(info) {
            location.href = "/event/" + info.event.id;
        },
        eventDidMount: function(arg) {
            const element = document.getElementById("checkbox-" + arg.event.extendedProps.category.name);
            const placeElement = document.getElementById("checkbox-place-" + arg.event.extendedProps.saved_location.name);
            let display = false;
            let atLeastOneChecked = false;
            for (accessibility of accessibilityList) {
                const accessibilityElement = document.getElementById("checkbox-" + accessibility);
                atLeastOneChecked |= accessibilityElement.checked;
                if (arg.event.extendedProps[accessibility] && accessibilityElement.checked) {
                    display = true;
                }
            }
            display |= !atLeastOneChecked;
            display &= (element.checked && placeElement.checked);
            if (!display) {
                arg.el.style.display = "none";
            }

            const dotEl = arg.el.getElementsByClassName('fc-list-event-dot')[0];
            if (dotEl) {
                dotEl.style.borderColor = colors[arg.event.extendedProps.saved_location.name];
                // dotEl.style.backgroundColor = colors[arg.event.extendedProps.saved_location.name];
            }
            else {
                arg.el.style.backgroundColor = colors[arg.event.extendedProps.saved_location.name];
            }

            if (screen.width > 900 && arg.view.type !== "listMonth") {
                const span = document.createElement("span");
                span.textContent = "📍" + arg.event.extendedProps.location;
                arg.el.getElementsByClassName("fc-event-main-frame")[0].append(span);
            }
            arg.el.style.cursor = "pointer";
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