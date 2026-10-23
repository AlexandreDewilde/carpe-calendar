const colors = {};

const accessibilityList = ["blind_friendly", "deaf_friendly", "pmr_friendly", "neurodiversity_friendly"];

// Each place always gets the same color, picked from its name
const placeColors = [
    "#C52224",
    "#1F77B4",
    "#2CA02C",
    "#9467BD",
    "#FF7F0E",
    "#17BECF",
    "#8C564B",
    "#E377C2",
    "#BCBD22",
    "#7F7F7F",
];

// UCLouvain week system, edited in the admin (AcademicPeriod)
const academicPeriods = JSON.parse(document.getElementById("academic-periods").textContent).map((period) => ({
    ...period,
    start: parseLocalDate(period.start),
    end: parseLocalDate(period.end),
}));

function parseLocalDate(isoDate) {
    const [year, month, day] = isoDate.split("-").map(Number);
    return new Date(year, month - 1, day);
}

const getWeekNumber = (d) => {
    const day = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const period = academicPeriods.find((p) => p.start <= day && day <= p.end);
    if (!period) {
        return "-";
    }
    if (!period.numbered) {
        return period.name;
    }
    // Round to absorb daylight saving time shifts
    const weeks = Math.floor(Math.round((day - period.start) / 86400000) / 7);
    return period.name + (period.first_week_number + weeks).toString();
}

function placeColor(name) {
    let hash = 0;
    for (const char of name) {
        hash = (hash * 31 + char.codePointAt(0)) | 0;
    }
    return placeColors[Math.abs(hash) % placeColors.length];
}

function initPlaceColors() {
    for (place of places) {
        colors[place] = placeColor(place);
        const dot = document.getElementById("dot-" + place);
        dot.style.backgroundColor = colors[place];
    }
}

// Checking a category checks all its subcategories, and a parent shows a partial state when only some are checked
function updateSubcategories(checkbox) {
    const children = checkbox.parentElement.querySelector(":scope > .category-children");
    if (children) {
        for (const child of children.querySelectorAll(".category-checkbox")) {
            child.checked = checkbox.checked;
            child.indeterminate = false;
        }
    }
    let group = checkbox.closest(".category-children");
    while (group) {
        const parent = group.parentElement.querySelector(":scope > .category-checkbox");
        const siblings = [...group.querySelectorAll(":scope > .form-check > .category-checkbox")];
        const checkedCount = siblings.filter((sibling) => sibling.checked && !sibling.indeterminate).length;
        parent.checked = checkedCount > 0 || siblings.some((sibling) => sibling.indeterminate);
        parent.indeterminate = parent.checked && checkedCount < siblings.length;
        group = parent.closest(".category-children");
    }
}

function createCalendar() {
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        themeSystem: 'bootstrap5',
        initialView: screen.width > 800 ? 'dayGridWeek' : 'dayGridDay',
        customButtons: {
            addEvent: {
                text: calendarText.addEvent,
                click: function() {
                    location.href = "/add-event";
                }
            },
            today: {
                text: calendarText.today,
                click: function() {
                    calendar.today();
                }
            }
        },
        locale: document.documentElement.lang,
        firstDay: 1,
        headerToolbar: {
            left: 'addEvent',
            center: 'title',
            right: 'dayGridDay,dayGridWeek,dayGridMonth,listMonth prev,today,next',
        },
        buttonText: {
            month: calendarText.month,
            listMonth: calendarText.list,
            week: calendarText.week,
            day: calendarText.day,
            today: calendarText.today,
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
        titleFormat: { day: 'numeric', year: 'numeric', month: 'long' },
        eventTimeFormat: { hour: 'numeric', minute: '2-digit', hour12: false },
        eventDisplay: 'block',
        displayEventEnd: true,
        eventSources : [
            {
                url: "/events",
            }
        ],
        eventClick: function(info) {
            location.href = "/event/" + info.event.id;
        },
        eventClassNames: 'carpe-event',
        eventContent: function(arg) {
            if (arg.view.type.startsWith("list")) {
                return true;
            }
            const block = document.createElement("div");
            block.className = "event-block";
            const time = document.createElement("div");
            time.className = "event-block-time";
            time.textContent = arg.timeText;
            const title = document.createElement("div");
            title.className = "event-block-title";
            title.textContent = arg.event.title;
            const place = document.createElement("div");
            place.className = "event-block-location";
            place.innerHTML = '<i class="fa-solid fa-location-dot"></i> ';
            place.append(arg.event.extendedProps.location);
            block.append(time, title, place);
            return { domNodes: [block] };
        },
        eventDidMount: function(arg) {
            const element = document.getElementById("checkbox-category-" + arg.event.extendedProps.category.id);
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
            display &= (element.checked && (placeElement?.checked ?? true));
            if (!display) {
                arg.el.style.display = "none";
            }

            const color = colors[arg.event.extendedProps.saved_location.name] ?? placeColor(arg.event.extendedProps.saved_location.name);
            arg.el.style.setProperty("--event-color", color);
            const dotEl = arg.el.getElementsByClassName('fc-list-event-dot')[0];
            if (dotEl) {
                dotEl.style.borderColor = color;
                const listTitle = arg.el.querySelector(".fc-list-event-title");
                const listLocation = document.createElement("span");
                listLocation.className = "event-list-location";
                listLocation.textContent = arg.event.extendedProps.location;
                listTitle.append(listLocation);
            }
            arg.el.style.cursor = "pointer";

            if (window.matchMedia("(hover: hover)").matches) {
                const tooltip = document.createElement("div");
                for (const line of [arg.event.title, "📍" + arg.event.extendedProps.location, arg.event.extendedProps.category.name + " · " + arg.event.extendedProps.organizer]) {
                    const lineEl = document.createElement("div");
                    lineEl.textContent = line;
                    tooltip.append(lineEl);
                }
                new mdb.Tooltip(arg.el, { title: tooltip, html: true, placement: "top" });
            }
        },
        eventWillUnmount: function(arg) {
            mdb.Tooltip.getInstance(arg.el)?.dispose();
        },
    });
    calendar.render();
    for (const checkbox of document.querySelectorAll(".category-checkbox")) {
        checkbox.addEventListener("change", function() {
            updateSubcategories(checkbox);
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