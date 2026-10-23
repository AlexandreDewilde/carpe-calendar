const addDate = document.getElementById('add-date');
const datesContainer = document.getElementById('dates-container');
const removeDate = document.getElementById('remove-date');

removeDate.addEventListener('click', function() {
    const dateForms = document.querySelectorAll('.date-form-container');
    if (dateForms.length > 1) {
        datesContainer.removeChild(dateForms[dateForms.length - 1]);
    }
});

// Translated labels, taken from the first date row
const startLabel = document.querySelector('label[for="start"]').textContent;
const endLabel = document.querySelector('label[for="end"]').textContent;

addDate.addEventListener('click', function() {
    const dateForm = document.createElement('div');
    dateForm.classList.add('mb-3', 'form-row', 'align-items-center', 'date-form-container');
    dateForm.innerHTML = `
        <div class="col-sm-3 my-1">
            <label class="form-label">${startLabel}</label>
            <input type="datetime-local" name="start" class="form-control">
        </div>
        <div class="col-sm-3 my-1">
            <label class="form-label">${endLabel}</label>
            <input type="datetime-local" name="end" class="form-control">
        </div>
    `;
    datesContainer.appendChild(dateForm);
});

function createBasicQrCode(data, image, color = "black") {
    console.log(data);
    return new QRCodeStyling({
        width: 500,
        height: 500,
        type: "canvas",
        data: data,
        image: image,
        dotsOptions: {
            color: color,
            type: "rounded"
        },
        backgroundOptions: {
            color: "#e9ebee",
        },
        imageOptions: {
            crossOrigin: "anonymous",
            margin: 20,
        }
    });
}

if (submitStatus === "success") {
    const carpeQrCode = createBasicQrCode(carpeLink, bubulleUrl);
    carpeQrCode.append(document.getElementById('qr-code-carpe'));

    if (facebookLink !== "" && facebookLink !== undefined) {
        const qrCode = createBasicQrCode(facebookLink, "https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg", "#4267b2");
        qrCode.append(document.getElementById('qr-code-facebook'));
    }
    if (formLink !== "" && formLink !== undefined) {
        const qrCode = createBasicQrCode(formLink, "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Google_Forms_2020_Logo.svg/70px-Google_Forms_2020_Logo.svg.png", "#642bbf");
        qrCode.append(document.getElementById('qr-code-form'));
    }
}