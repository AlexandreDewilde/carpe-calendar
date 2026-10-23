# Carpe Calendar

The [CarpeStudentem Calendar](https://agenda.carpestudentem.be/calendar/) is a community-driven event calendar designed for the city of Louvain-la-Neuve, Belgium.

![Calendar example](https://github.com/AlexandreDewilde/carpe-calendar/blob/main/doc/images/calendar.png?raw=true)

The primary objective of this project is to foster collaboration by allowing users to add their own events, which will then be reviewed and validated by administrators.

### Technologies Used

The project is built with:

- **Python 3.14** (3.12 minimum)
- **Django** (web framework)
- **SQLite** (database, limited concurrent user support)
- **Bootstrap** (frontend framework)
- **FullCalendar** (JavaScript library for event calendars)

## Installation

To run the project, ensure you have **Python 3.12** or higher installed.

1. Clone the repository:
   ```bash
   git clone https://github.com/AlexandreDewilde/carpe-calendar.git
   cd carpe-calendar
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Apply database migrations:
   ```bash
   python manage.py migrate
   ```

## Environment Variables

You need to configure two environment variables:

- `DJANGO_DEBUG`: Set to `0` for production, or `1` for development (debug mode).
- `DJANGO_SECRET_KEY`: Define your secret key for Django.

Optional, to email organizers the link to edit their event (no email is sent if `EMAIL_HOST` is empty):

- `EMAIL_HOST`, `EMAIL_PORT` (default `587`), `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` (default `1`)
- `DEFAULT_FROM_EMAIL`: sender address of the emails
- `EVENT_EDIT_LINK_DAYS`: number of days the edit link stays valid (default `30`)

## Running the Project

To start the development server, use:

```bash
python manage.py runserver
```

## Contributions

Contributions are welcome! Feel free to submit issues, suggestions, open issues, or pull requests to improve the project.

## TODO


* add week number according to uclouvain week system
* subcategory
* export to ics
* better visualization of event and add event page
* export week as image (png, jpg) from psd template
* internalization
* auto translate of title with deepl?
* Add Progressive web app
* Remake the event page design
* better display of event block on calendar
* tooltip for pc user
* place selection existing one, else fill text
* add map or link to open map app
* captcha
* a second calendar for registration limit
* event update (link send to organizer then update for a fixed limit time period)
