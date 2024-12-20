# CalMate - Calories, Macros and Mates

CalMate is a comprehensive AI-based fitness tracking application that combines calorie counting, macro tracking, and social features to help users achieve their fitness goals together. Built with FastAPI and Appwrite, it provides a robust backend API for managing user fitness data and social interactions.

## Features

- **Authentication System**
  - User signup and login
  - Secure token-based authentication
  - Logout functionality
- **Food Tracking**
  - AI-powered food image analysis
  - Calorie and macro tracking
  - Historical food logs
- **Social Features**
  - Friend requests and connections
  - Social feed of friends' activities
  - Activity sharing
- **Fitness Goals**
  - Daily calorie goal setting
  - Progress tracking
  - Current status monitoring
- **Streaks & Gamification**
  - Daily streak tracking
  - Leaderboard system
  - Achievement system

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: Appwrite
- **Authentication**: Appwrite Auth
- **Storage**: Appwrite Storage
- **AI Integration**: OpenAI API

## Prerequisites

- Python 3.8+
- Appwrite Instance
- OpenAI API Key

## Environment Setup

1. Clone the repository
2. Copy `.env.example` to `.env`
3. Configure the following environment variables:

```env
MAX_UPLOAD_SIZE=5242880

# App Configuration
APP_NAME=CalMate
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-super-secret-key

# Appwrite Configuration
APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=project-id
APPWRITE_API_KEY=api-key
APPWRITE_BUCKET_ID=bucket-id

# OpenAI Configuration
OPENAI_API_KEY=api-key

# Firebase Configuration (for notifications)
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
FIREBASE_API_KEY=api-key

# Database Configuration
DATABASE_ID=db-id

# Storage Configuration
STORAGE_BUCKET=bucket-name

# Server Configuration
HOST=0.0.0.0
PORT=8000

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Rate Limiting
RATE_LIMIT_PER_SECOND=10

# Cache Settings
CACHE_TTL=3600

# Image Upload Settings
ALLOWED_IMAGE_TYPES=image/jpeg,image/png,image/gif

# Notification Settings
NOTIFICATION_EMAIL=your-email
```

## Installation

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/signup` - Create new user account
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout

### Food Tracking

- `POST /api/v1/food/analyze` - Analyze food image
- `GET /api/v1/food/logs` - Get food logging history

### Social Features

- `POST /api/v1/social/friends/request/{user_id}` - Send friend request
- `POST /api/v1/social/friends/accept/{request_id}` - Accept friend request
- `GET /api/v1/social/friends` - Get friends list
- `GET /api/v1/social/feed` - Get social feed

### User Profile & Goals

- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update user profile
- `POST /api/v1/users/calorie-goal` - Set daily calorie goal
- `GET /api/v1/users/calorie-status` - Get current calorie status

### Streaks & Achievements

- `GET /api/v1/streaks/current` - Get current streak
- `GET /api/v1/streaks/leaderboard` - Get streaks leaderboard

## Configuration Options

### Upload Settings

- Maximum upload size: 5MB
- Allowed image types: JPEG, PNG, GIF

### Rate Limiting

- Default: 10 requests per second per user

### Caching

- Default TTL: 3600 seconds (1 hour)

## Error Handling

The API uses standard HTTP status codes and returns JSON responses with the following structure:

```json
{
    "status": "error",
    "message": "Error description",
    "code": "ERROR_CODE"
}
```

## Swagger

Access the Swagger UI at [https://calmate-app.vercel.app/docs](https://calmate-app.vercel.app/docs)

## ReDoc

Access the ReDoc documentation at [https://calmate-app.vercel.app/redoc](https://calmate-app.vercel.app/docs)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For support, email [huzaifa.coder785@gmail.com](mailto:huzaifa.coder785@gmail.com) or create an issue in the repository.

