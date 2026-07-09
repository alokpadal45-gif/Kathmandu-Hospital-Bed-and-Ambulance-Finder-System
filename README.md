# Kathmandu Emergency Bed and Ambulance Finder System

A real-time web application that lets citizens find hospitals with available
beds, ICU capacity, and ambulances during emergencies — removing the delay of
calling hospitals one by one. Hospital staff update resource availability
live; citizens and admins see those changes reflected instantly via
WebSockets.

Built for PRG 100: System Analysis & Design (Westcliff University).

## Stakeholders

- **Citizens** — search hospitals, view live bed/ICU/ambulance availability, request an ambulance, track request status.
- **Hospital Staff** — update their hospital's bed/ICU/ambulance availability, accept/reject incoming ambulance requests.
- **System Administrator** — manage hospitals and staff accounts, view system-wide reports.
- **Health Authority** *(future enhancement)* — read-only oversight dashboard.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Django, Django REST Framework |
| Real-time | Django Channels + Daphne (ASGI/WebSockets) |
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript |
| Database | SQLite (development) → MySQL (production) |
| Version Control | Git & GitHub |

## Project Structure

```
kathmandu_emergency_system/
├── config/                  # Project configuration
│   ├── settings/
│   │   ├── base.py          # Shared settings
│   │   ├── development.py   # Local dev (SQLite, in-memory channel layer)
│   │   └── production.py    # Production (MySQL, Redis channel layer)
│   ├── asgi.py               # Daphne entry point + Channels routing
│   ├── wsgi.py
│   └── urls.py
├── apps/
│   ├── accounts/             # Custom User model, roles, auth
│   ├── hospitals/            # Hospital, Bed, ICU, Ambulance models
│   ├── ambulances/           # Ambulance request & tracking workflow
│   ├── dashboard/            # Role-based dashboard views
│   └── api/                  # DRF serializers/viewsets + Channels consumers
├── templates/                 # HTML templates, organized per app
├── static/                    # CSS, JS, images
├── media/                     # User-uploaded files (hospital images, etc.)
├── requirements/               # base / development / production dependency lists
├── .env.example                # Documents required environment variables
└── manage.py
```

## Getting Started (Development)

1. **Clone and enter the project**
   ```bash
   git clone <your-repo-url>
   cd kathmandu_emergency_system
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements/development.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # then edit .env and set SECRET_KEY (and other values as needed)
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (for the admin module)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```
   Visit `http://127.0.0.1:8000/`

## Build Status

This project is being built in stages. Progress so far:

- [x] Step 1 — Project scaffolding, settings split, git, requirements
- [ ] Step 2 — Accounts app (custom User model, roles, auth)
- [ ] Step 3 — Hospitals app (models)
- [ ] Step 4 — Ambulance Requests app
- [ ] Step 5 — REST API layer
- [ ] Step 6 — Real-time layer (Django Channels)
- [ ] Step 7 — Citizen frontend
- [ ] Step 8 — Hospital Staff dashboard
- [ ] Step 9 — Admin dashboard
- [ ] Step 10 — Testing & deployment config

## Author

Alok Padal — Westcliff University, PRG 100: System Analysis & Design, Professor Vaidhya
