# Venue Hunt

Venue Hunt is a comprehensive venue recommendation and booking system built with Django. The platform connects event organizers with venue owners, making it easy to find and book venues for various events.

## Features

### For Event Organizers
- Search and filter venues based on various criteria
- View detailed venue information and photos
- Make booking requests
- Track booking status
- Leave reviews and ratings

### For Venue Owners
- Create and manage venue listings
- Upload venue photos
- Handle booking requests
- Track venue performance and reviews

## Technical Stack
- Backend: Django
- Frontend: HTML, CSS
- Database: SQLite (development)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd venuehunt
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

Visit http://localhost:8000 to access the application.

## Project Structure
```
venuehunt/
├── accounts/         # User authentication and profiles
├── venues/          # Venue management
├── bookings/        # Booking system
├── static/          # Static files (CSS, JS, images)
├── templates/       # HTML templates
└── venuehunt/      # Project settings
```

## License
[MIT License](LICENSE)
