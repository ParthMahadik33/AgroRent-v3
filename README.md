# AgroRent - Farm Machinery Rental Platform

A Flask-based web application for renting farm machinery.

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   python app.py
   ```

3. **Access the Application**
   - Open your browser and navigate to: `http://localhost:5000`
   - Sign up for a new account or sign in with existing credentials

## Features

- User registration with email validation
- Secure password hashing
- User authentication and session management
- SQLite database for user storage
- Flash messages for user feedback

## Database

The application uses SQLite and automatically creates the database file (`agrorent.db`) on first run.

## Routes

- `/` - Home page
- `/signup` - User registration
- `/signin` - User login
- `/signout` - User logout

