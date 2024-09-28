
for (const date of dates) {
    const [start, end] = date.split(" - ");
    const startDatetime = new Date(start);
    const endDatetime = new Date(end);

    const datesTbody = document.getElementById("dates-tbody");
    const tr = document.createElement("tr");
    const tdStart = document.createElement("td");
    tdStart.textContent = startDatetime.toLocaleString();
    const tdEnd = document.createElement("td");
    tdEnd.textContent = endDatetime.toLocaleString();
    tr.appendChild(tdStart);
    tr.appendChild(tdEnd);
    datesTbody.appendChild(tr);
}