# Airbnb Clone - Flask Backend API

A comprehensive RESTful API backend for an Airbnb-like vacation rental application built with Flask.

## Features

- ✅ User authentication & authorization (JWT)
- ✅ Property listings management
- ✅ Booking system with availability checking
- ✅ Review & rating system
- ✅ Payment integration placeholder (Stripe ready)
- ✅ Image upload support
- ✅ Search & filtering
- ✅ Rate limiting
- ✅ CORS enabled
- ✅ PostgreSQL database

## Tech Stack

- **Framework**: Flask 3.0
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Authentication**: Flask-JWT-Extended
- **Password Hashing**: Flask-Bcrypt
- **Migrations**: Flask-Migrate
- **API Documentation**: Built-in endpoints
- **Rate Limiting**: Flask-Limiter with Redis
- **File Storage**: AWS S3 ready
- **Payments**: Stripe ready

## Project Structure

```
airbnb-backend/
├── app/
│   ├── __init__.py           # App factory
│   ├── models/               # Database models
│   │   ├── user.py
│   │   ├── property.py
│   │   ├── booking.py
│   │   └── review.py
│   └── api/                  # API routes
│       ├── auth/            # Authentication
│       ├── users/           # User management
│       ├── properties/      # Property listings
│       ├── bookings/        # Booking management
│       ├── reviews/         # Reviews & ratings
│       └── payments/        # Payment processing
├── config.py                # Configuration
├── extensions.py            # Flask extensions
├── requirements.txt         # Dependencies
├── run.py                   # Entry point
└── .env.example            # Environment variables template
```

## Installation & Setup

### 1. Prerequisites

- Python 3.8+
- PostgreSQL
- Redis (for rate limiting)

### 2. Clone & Setup

```bash
# Navigate to your projects directory
cd ~/Documents/projects/

# Create project directory
mkdir airbnb-backend
cd airbnb-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb airbnb_dev

# Or using psql
psql -U postgres
CREATE DATABASE airbnb_dev;
\q
```

### 4. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

Required environment variables:
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=postgresql://username:password@localhost:5432/airbnb_dev
REDIS_URL=redis://localhost:6379/0
```

### 5. Initialize Database

```bash
# Initialize migrations
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migrations
flask db upgrade
```

### 6. Run the Application

```bash
# Development server
python run.py

# Or using Flask CLI
flask run
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user
- `POST /api/auth/change-password` - Change password
- `POST /api/auth/logout` - Logout

### Users
- `GET /api/users/<id>` - Get user profile
- `PUT /api/users/me` - Update profile

### Properties
- `GET /api/properties` - List all properties (with filters)
- `GET /api/properties/<id>` - Get property details
- `POST /api/properties` - Create property (auth required)
- `PUT /api/properties/<id>` - Update property (host only)
- `DELETE /api/properties/<id>` - Delete property (host only)
- `GET /api/properties/<id>/availability` - Check availability
- `GET /api/properties/my-properties` - Get user's properties

### Bookings
- `POST /api/bookings` - Create booking (auth required)
- `GET /api/bookings/my-bookings` - Get user's bookings
- `GET /api/bookings/<id>` - Get booking details
- `POST /api/bookings/<id>/cancel` - Cancel booking

### Reviews
- `POST /api/reviews` - Create review (auth required)
- `GET /api/reviews/property/<id>` - Get property reviews
- `POST /api/reviews/<id>/response` - Add host response

### Payments
- `POST /api/payments/create-payment-intent` - Create payment (Stripe)
- `POST /api/payments/webhook` - Stripe webhook handler

## Example API Calls

### Register User
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePassword123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123"
  }'
```

### Create Property (with JWT token)
```bash
curl -X POST http://localhost:5000/api/properties \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "Beautiful Beach House",
    "description": "A stunning beachfront property",
    "property_type": "house",
    "address": "123 Beach Road",
    "city": "Miami",
    "country": "USA",
    "bedrooms": 3,
    "bathrooms": 2,
    "max_guests": 6,
    "price_per_night": 150.00
  }'
```

### Search Properties
```bash
curl "http://localhost:5000/api/properties?city=Miami&bedrooms=2&max_price=200"
```

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## Deployment

### Production Configuration

1. Set environment to production:
```env
FLASK_ENV=production
```

2. Use a production WSGI server:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

3. Set up reverse proxy (Nginx recommended)

### Docker Deployment

```dockerfile
# Coming soon
```

## Security Features

- Password hashing with bcrypt
- JWT token authentication
- Rate limiting per endpoint
- CORS configuration
- SQL injection protection (SQLAlchemy ORM)
- Input validation
- Environment variable management

## Next Steps

1. **Implement Stripe Payment Integration**
   - Complete payment intent creation
   - Handle webhooks
   - Manage refunds

2. **Add File Upload**
   - AWS S3 integration for property images
   - Image processing and optimization

3. **Add Email Notifications**
   - Booking confirmations
   - Password reset
   - Review notifications

4. **Add Search Enhancements**
   - Full-text search
   - Location-based search
   - Advanced filters

5. **Add Admin Panel**
   - User management
   - Property moderation
   - Analytics dashboard

## Contributing

Contributions welcome! Please follow the standard Git workflow:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use this project for learning or commercial purposes.

## Support

For questions or issues, please open an issue on GitHub or contact the development team.

---

**Happy Coding! 🚀**
