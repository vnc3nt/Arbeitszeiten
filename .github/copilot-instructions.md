# Arbeitszeiten (Working Hours Tracker) 

Arbeitszeiten is a Flask-based web application for tracking working hours and time entries. It features a PostgreSQL backend with a REST API and a responsive web frontend with Node.js build tools.

**ALWAYS follow these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Bootstrap and Setup
- **REQUIRED**: Install Python 3.12.3 (specified in `.python-version`)
- **REQUIRED**: Install Node.js (tested with v20.19.5)
- **REQUIRED**: Install PostgreSQL server or prepare SQLite for development
- Install Python dependencies: `pip install -r requirements.txt` - takes 30-60 seconds normally
- Install Node.js dependencies: `npm install` - takes 30-60 seconds, creates `node_modules/` and `package-lock.json`

### Database Setup
**CRITICAL DATABASE CONFIGURATION ISSUE**: The application uses a non-standard PostgreSQL URI format that requires specific setup.

**PostgreSQL (Required for Production):**
- The application REQUIRES a `.env` file for database configuration
- **UNUSUAL FORMAT**: Database URI is `postgresql://{uname}.{db}:{password}@{host}:{port}/{scheme}`
- This creates usernames like `username.dbname` which is non-standard
- Create PostgreSQL user matching this format:
  ```bash
  sudo -u postgres createuser "your_username.your_db" 
  sudo -u postgres createdb arbeitszeiten -O "your_username.your_db"
  sudo -u postgres psql -c "ALTER USER \"your_username.your_db\" PASSWORD 'your_password';"
  ```
- Create `.env` file with exact format:
  ```
  uname=your_username
  db=your_db
  password=your_password
  host=localhost
  port=5432
  scheme=arbeitszeiten
  debug=True
  ```

**SQLite (Development Workaround):**
- The application CANNOT run without a `.env` file
- For development, modify `main.py` temporarily:
  ```python
  # Replace the database URI configuration with:
  app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///arbeitszeiten.db"
  ```
- This bypasses the unusual PostgreSQL format requirement

### Running the Application
- **PREREQUISITE**: Create `.env` file with database configuration (see Database Setup section)
- **Backend**: `python main.py` - starts Flask server on http://localhost:8080
- **CRITICAL**: Application WILL FAIL without proper `.env` file and database setup
- **Frontend Build**: `npm run build` - FAILS because `templates/snippets/data.html` is missing (expected behavior)
- **Frontend Dev**: `npm run dev` - FAILS for same reason (this is a known issue)
- **NEVER CANCEL**: Application startup takes 5-10 seconds. Database creation is automatic on first run.
- **NEVER CANCEL**: If database connection fails, expect 15-30 seconds for timeout

### Application Structure
- **Main entry**: `main.py` - Flask application with database initialization
- **Database models**: `models.py` - SQLAlchemy models for users, data, categories, tokens
- **Authentication**: `login.py` - User authentication, session management, password hashing
- **API endpoints**: `api.py` and `api_resources/` - REST API for data access
- **Frontend**: `templates/` - Jinja2 templates, `static/` - CSS, JavaScript, images
- **Configuration**: `constants.py` - Application constants and regex patterns

## Validation and Testing

### Manual Testing Scenarios
- **ALWAYS test the complete user workflow after making changes:**
  1. Start the application: `python main.py`
  2. Navigate to http://localhost:8080 (should redirect to /login)
  3. Create a new account via the register page
  4. Log in with the new account
  5. Access the home page and verify time entry functionality
  6. Test the API endpoint: `curl http://localhost:8080/api/` should return `{"info": "api is there"}`

### Known Issues and Limitations
- **NPM build failure**: `npm run build` and `npm run dev` fail because `templates/snippets/data.html` is missing
- **Database configuration**: The PostgreSQL URI format is non-standard and requires the `db` field to be empty
- **No unit tests**: The repository contains no test files or testing infrastructure
- **Frontend build**: The Parcel build system is configured but the target file doesn't exist

### Build Times and Timeouts
- **Python dependency installation**: 30-60 seconds - NEVER CANCEL, set timeout to 120+ seconds
- **Node.js dependency installation**: 30-60 seconds - NEVER CANCEL, set timeout to 120+ seconds  
- **Application startup**: 5-10 seconds - NEVER CANCEL, set timeout to 30+ seconds
- **Database initialization**: 2-5 seconds on first run

## Key Components and Navigation

### Backend Files
- `main.py` - Main Flask application (549 lines)
- `models.py` - Database models (38 lines)
- `login.py` - Authentication logic (120 lines)
- `api.py` - API blueprint setup (11 lines)
- `api_resources/` - API resource implementations
- `constants.py` - Configuration constants (8 lines)

### Frontend Files
- `templates/index.html` - Base template with responsive design
- `templates/home.html` - Main dashboard for time tracking
- `templates/login.html` - User login form
- `templates/register.html` - User registration form
- `templates/profile.html` - User profile management
- `static/css/style.css` - Main stylesheet with dark/light mode support
- `static/script/regex.js` - Client-side validation (163 lines)

### Database Schema
- `users` - User accounts (id, username, password)
- `data` - Time entries (userid, date, categoryid, data, maxhours)
- `category` - Time categories (id, userid, name, color)
- `token` - Session tokens (userid, token, expiretime)

## Common Tasks and Commands

### Development Workflow
- Start development server: `python main.py`
- Access application: http://localhost:8080
- Check API health: `curl http://localhost:8080/api/`
- View database entries: Direct SQLite/PostgreSQL query tools

### File Modifications
- **Database changes**: Modify `models.py`, then restart application for schema updates
- **API changes**: Modify files in `api_resources/`, restart application
- **Frontend changes**: Modify templates or static files, reload browser
- **Authentication changes**: Modify `login.py`, restart application

### Environment Configuration
- **Development**: Use SQLite with modified `main.py` for easier setup
- **Production**: Use PostgreSQL with proper `.env` configuration
- **Debug mode**: Set `debug=True` in `.env` file

## File System Layout
```
├── .env                 # Database configuration (create manually)
├── .gitignore          # Excludes node_modules, __pycache__, .env, etc.
├── .python-version     # Specifies Python 3.12.3
├── api.py              # API blueprint setup
├── api_resources/      # API endpoint implementations
├── constants.py        # Application constants
├── login.py            # Authentication and session management
├── main.py             # Main Flask application
├── models.py           # SQLAlchemy database models  
├── package.json        # Node.js dependencies (Parcel, Chart.js)
├── requirements.txt    # Python dependencies (Flask, SQLAlchemy, PostgreSQL)
├── static/             # CSS, JavaScript, images
├── templates/          # Jinja2 HTML templates
└── tools/              # Utility scripts (CSV converter)
```

## Troubleshooting

**Application Won't Start - Database Issues**
- **MOST COMMON**: Missing `.env` file - application requires database configuration
- **Error "ValueError: invalid literal for int()"**: Empty port in .env file - check all fields are filled
- **Error "password authentication failed for user"**: PostgreSQL user doesn't match the unusual format
- **Solution**: Use SQLite workaround by modifying `main.py` database URI for development

**PostgreSQL Connection Issues**
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check `.env` file format - use the exact format shown in Database Setup
- Remember the username format is `username.dbname` (unusual but required)
- For development, switch to SQLite by modifying the database URI in `main.py`

**Frontend Build Issues**
- `npm run build` failures are expected due to missing `templates/snippets/data.html`
- The application runs without the frontend build system
- Static files are served directly by Flask in development mode

**Application Won't Start - Python Issues**
- Check Python version: `python --version` (should be 3.12.3)
- Verify dependencies: `pip list | grep -E "(Flask|SQLAlchemy)"`
- Install missing dependencies: `pip install -r requirements.txt`

**Always validate changes by running through the complete user registration and login workflow.**