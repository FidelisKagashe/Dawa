# Hospital Medicine Management System

A comprehensive Django-based web application for managing hospital medication schedules, patient compliance tracking, and automated SMS notifications.

## Features

### Patient Features
- Personal medication dashboard with daily schedule
- Medication intake confirmation with timestamps
- Complete treatment history and progress tracking
- SMS reminders for medication times
- Access to personal progress reports

### Hospital Admin Features
- Patient management and medical record tracking
- Prescription creation and medication scheduling
- Real-time compliance monitoring and alerts
- Comprehensive reporting system with PDF export
- Manual SMS notification system
- System-wide analytics and patient outcomes

### Automated Systems
- SMS reminders sent 15 minutes before medication times
- Missed medication alerts for high-priority prescriptions
- Daily medication schedule generation
- Automatic progress report generation

## Technology Stack

- **Backend**: Django 4.2.7
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: Django Templates with Bootstrap 5
- **SMS Service**: Twilio
- **Task Queue**: Celery with Redis
- **PDF Generation**: ReportLab
- **Styling**: Bootstrap 5 with custom CSS

## Installation

### Prerequisites
- Python 3.8+
- Redis (for Celery tasks)
- Twilio account (for SMS)

### Setup Instructions

1. **Clone and setup the project:**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Copy environment variables
   cp .env.example .env
   ```

2. **Configure environment variables in `.env`:**
   ```
   SECRET_KEY=your-django-secret-key
   DEBUG=True
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   ```

3. **Initialize the database:**
   ```bash
   python manage.py migrate
   python management_commands.py  # Creates sample data
   ```

4. **Create directories:**
   ```bash
   mkdir -p logs media/reports
   ```

5. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Start Celery worker (in separate terminal):**
   ```bash
   celery -A hospital_system worker --loglevel=info
   ```

7. **Start Celery beat scheduler (in separate terminal):**
   ```bash
   celery -A hospital_system beat --loglevel=info
   ```

## Usage

### Access the System
- **Admin Login**: username=`admin`, password=`admin123`
- **Patient Login**: username=`patient1`, password=`patient123`
- **Django Admin**: http://127.0.0.1:8000/admin/

### Creating Prescriptions
1. Login as admin
2. Navigate to "New Prescription"
3. Select patient, medication, dosage, and frequency
4. Set priority level and special instructions
5. The system automatically creates medication schedules

### Patient Workflow
1. Patients receive SMS reminders 15 minutes before medication time
2. Patients login to confirm medication intake
3. System tracks compliance and generates progress reports
4. Missed medications trigger alerts for high-priority prescriptions

### SMS Notifications
The system automatically sends:
- Medication reminders (15 minutes before)
- Missed medication alerts (1 hour after)
- Treatment completion notifications
- Manual admin notifications

## Database Models

### Core Models
- **User**: Extended Django user with patient/admin roles
- **PatientProfile**: Additional patient information
- **Medication**: Drug information and details
- **Prescription**: Patient medication assignments
- **MedicationSchedule**: Daily time schedules for prescriptions
- **MedicationIntake**: Individual medication intake records
- **SMSNotification**: SMS delivery tracking
- **ProgressReport**: Patient compliance and progress reports

## API Endpoints

### Patient Endpoints
- `/medications/dashboard/` - Patient dashboard
- `/medications/history/` - Medication history
- `/medications/intake/confirm/<id>/` - Confirm medication intake

### Admin Endpoints
- `/medications/admin-dashboard/` - Admin dashboard
- `/medications/prescription/create/` - Create prescription
- `/medications/admin/patient/<id>/` - Patient details
- `/reports/generate/<patient_id>/` - Generate progress report

## Security Features

- Django's built-in CSRF protection
- Role-based access control (patients vs admins)
- Secure SMS credential management
- User session management
- Input validation and sanitization

## Deployment Considerations

### Production Settings
- Use PostgreSQL database
- Configure proper SECRET_KEY
- Set DEBUG=False
- Use environment variables for sensitive data
- Setup proper logging
- Configure Celery with Redis in production

### Required Services
- Redis server for Celery
- Twilio account for SMS
- Web server (Nginx/Apache)
- Process manager (Supervisor/systemd)

## License

This project is for educational and demonstration purposes.