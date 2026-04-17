# Authentication & History Feature Guide

## Overview
The NutriNova AI application now includes a complete user authentication system with food analysis history tracking. Users can register, login, and maintain a personalized history of all their food analyses.

## Features Added

### 1. User Authentication
- **Registration**: New users can create accounts with username, email, and password
- **Login**: Secure login using username/email and password
- **Logout**: Safe logout functionality that clears session data
- **Session Management**: Persistent sessions using Flask's secure session cookies

### 2. Password Security
- All passwords are hashed using Werkzeug's `generate_password_hash()` 
- Passwords are never stored in plain text
- Secure password verification using `check_password_hash()`

### 3. Food Analysis History
- Automatic saving of all food analyses when user is logged in
- Complete nutrition data stored (calories, protein, fat, carbs, fiber, sugar, sodium, cholesterol)
- AI dietary advice preserved for each analysis
- Timestamp tracking for when each analysis was performed

### 4. History Viewing
- Beautiful modal interface to view all past analyses
- Displays food name, confidence score, and timestamp
- Shows key nutrients in an organized card layout
- Includes the full AI dietary analysis for each entry
- Responsive design matching the app's aesthetic

## Database Structure

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Food History Table
```sql
CREATE TABLE food_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    food_name TEXT NOT NULL,
    confidence REAL,
    calories TEXT,
    protein TEXT,
    fat TEXT,
    carbohydrates TEXT,
    fiber TEXT,
    sugar TEXT,
    sodium TEXT,
    cholesterol TEXT,
    dietary_advice TEXT,
    image_url TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
```

## API Endpoints

### Authentication Endpoints

#### POST /register
Register a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepass123"
}
```

**Response (Success - 201):**
```json
{
  "message": "Registration successful! Please log in."
}
```

**Response (Error - 409):**
```json
{
  "error": "Username or email already exists"
}
```

---

#### POST /login
Authenticate user and create session.

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "securepass123"
}
```

**Response (Success - 200):**
```json
{
  "message": "Login successful!",
  "username": "john_doe"
}
```

**Response (Error - 401):**
```json
{
  "error": "Invalid username/email or password"
}
```

---

#### POST /logout
End user session.

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

#### GET /check-auth
Check if user is currently logged in.

**Response (Logged In - 200):**
```json
{
  "logged_in": true,
  "username": "john_doe"
}
```

**Response (Not Logged In - 200):**
```json
{
  "logged_in": false
}
```

---

### History Endpoints

#### GET /history
Retrieve user's food analysis history (requires authentication).

**Headers:** Session cookie required

**Response (Success - 200):**
```json
{
  "history": [
    {
      "id": 1,
      "food_name": "Pizza",
      "confidence": 95.5,
      "calories": "266",
      "protein": "11.2",
      "fat": "10.5",
      "carbohydrates": "33.8",
      "fiber": "2.1",
      "sugar": "3.5",
      "sodium": "598",
      "cholesterol": "17",
      "dietary_advice": "...",
      "analyzed_at": "2025-04-06 14:30:00"
    }
  ],
  "count": 1
}
```

**Response (Not Authenticated - 401):**
```json
{
  "error": "Please log in to access this feature"
}
```

---

#### DELETE /history/<id>
Delete a specific history item (requires authentication).

**Response (Success - 200):**
```json
{
  "message": "History item deleted successfully"
}
```

**Response (Not Found - 404):**
```json
{
  "error": "History item not found"
}
```

---

## User Interface

### Login/Register Page (`/auth`)
- Modern, dark-themed authentication interface
- Tabbed interface for easy switching between Login and Register
- Form validation with helpful error messages
- Success notifications with automatic redirection
- Seamless integration with app's visual design

### Main App Updates
- **Navigation Bar**: Dynamic menu showing Login button or user menu based on auth status
- **User Menu**: When logged in, shows:
  - History button to view past analyses
  - Logout button to end session
- **Guest Menu**: When not logged in, shows Login button

### History Modal
- Full-screen overlay with scrollable content
- Displays all food analyses in chronological order (newest first)
- Each entry shows:
  - Food name and analysis timestamp
  - Confidence score
  - Key nutrients (Calories, Protein, Fat, Carbs) in card format
  - Complete AI dietary advice
- Close button or ESC key to dismiss
- Empty state message when no history exists

## How It Works

### Registration Flow
1. User navigates to `/auth` page
2. Fills in username, email, and password (min 6 characters)
3. System validates input and checks for duplicates
4. Password is hashed using Werkzeug security
5. User record created in database
6. User redirected to login tab with pre-filled username

### Login Flow
1. User enters username/email and password
2. System looks up user by username OR email
3. Password hash verified against stored hash
4. If valid, session created with user_id and username
5. User redirected to main app with authenticated menu

### Food Analysis with History
1. User uploads/selects food image
2. Image classified using ML model
3. Nutrition data fetched from USDA API
4. AI generates dietary advice via Gemini
5. **If user is logged in**: Analysis saved to database
6. Results displayed to user
7. Food context available for chatbot

### History Retrieval
1. User clicks "History" in navigation
2. Modal opens and fetches data from `/history` endpoint
3. Server queries database for user's analyses (ordered by date)
4. Data formatted and displayed in cards
5. Each card shows complete analysis details

## Security Features

1. **Password Hashing**: All passwords hashed with Werkzeug's secure algorithm
2. **SQL Injection Prevention**: Parameterized queries used throughout
3. **Session Security**: Flask secret key for signed cookies
4. **Authentication Checks**: Protected routes verify user session
5. **User Isolation**: Users can only access their own history

## Testing the Features

### Test Registration
1. Navigate to `http://127.0.0.1:5000/auth`
2. Click "Register" tab
3. Enter unique username, email, and password (6+ chars)
4. Click "Create Account"
5. Should see success message and auto-switch to login

### Test Login
1. On auth page, ensure "Login" tab is active
2. Enter your username/email and password
3. Click "Sign In"
4. Should redirect to main page with user menu visible

### Test Food Analysis
1. While logged in, go to Analyzer section
2. Upload a food image or enter URL
3. Click "Analyze Nutrition"
4. Wait for results
5. Analysis is automatically saved to your history

### Test History View
1. Click "History" in navigation bar (when logged in)
2. Modal should open showing all your analyses
3. Each entry displays food name, date, nutrients, and AI advice
4. Press ESC or click Close to dismiss

### Test Logout
1. Click "Logout" in navigation
2. Confirm the action
3. Should return to guest menu
4. Try accessing history - should require login

## File Structure

```
Major Project/
├── app.py                    # Main Flask application (UPDATED)
├── nutrition_app.db          # SQLite database (AUTO-CREATED)
├── templates/
│   ├── index.html           # Main app page (UPDATED)
│   └── auth.html            # Login/Register page (NEW)
├── rag_system.py            # RAG system (unchanged)
└── nutrition_knowledge/     # Knowledge base files (unchanged)
```

## Important Notes

1. **Database Auto-Creation**: The SQLite database (`nutrition_app.db`) is automatically created when the app starts
2. **No Migration Needed**: Existing functionality remains unchanged for non-logged-in users
3. **Backward Compatible**: Users can still analyze food without logging in (history just won't be saved)
4. **Session Persistence**: Sessions persist until browser is closed or user logs out
5. **Mobile Responsive**: All new UI elements work on mobile devices

## Troubleshooting

### Can't Register
- Check that username and email are unique
- Ensure password is at least 6 characters
- Verify server is running on port 5000

### Login Fails
- Double-check username/email and password
- Remember that passwords are case-sensitive
- Try registering a new account if you forgot credentials

### History Not Saving
- Ensure you're logged in before analyzing food
- Check browser console for any errors
- Verify session is active (user menu should be visible)

### History Modal Won't Open
- Make sure you're logged in
- Check network tab for API errors
- Try refreshing the page

## Future Enhancements (Optional)

Potential improvements for future versions:
- Email verification for registration
- Password reset functionality
- Profile page with user settings
- Export history as CSV/PDF
- Statistics dashboard (most analyzed foods, nutrition trends)
- Delete individual history items from UI
- Search/filter history by food name or date range
- Share analysis results with others
