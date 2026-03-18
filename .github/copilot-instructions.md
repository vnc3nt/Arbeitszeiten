# Arbeitszeiten - Time Tracking Web Application

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Application Overview
Arbeitszeiten is a Flask-based web application for tracking work hours with PostgreSQL database backend and Parcel-bundled frontend assets. The application provides user authentication, time tracking, and data visualization features.

## Working Effectively

### Initial Setup (Required for ALL work)
Bootstrap the development environment with these exact commands:

```bash
# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
**TIMING**: Python setup takes ~3 minutes total. NEVER CANCEL. Set timeout to 600+ seconds.
**NOTE**: pip install may fail due to PyPI connectivity issues. If pip install fails with timeouts, retry the command or use alternative PyPI mirrors.

```bash
# Install Node.js dependencies  
npm install
```
**TIMING**: npm install takes ~3 seconds. NEVER CANCEL.

### Database Setup (Required for Flask app)
Set up PostgreSQL database before running the Flask application:

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt-get update && sudo apt-get install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql

# Create database user and database
sudo -u postgres psql -c "CREATE USER test WITH PASSWORD 'testpass';"
sudo -u postgres psql -c "ALTER USER test CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE arbeitszeiten_db OWNER test;"
```

### Environment Configuration
Create `.env` file with database credentials:

```bash
echo -e "uname=test\ndb=\npassword=testpass\nhost=localhost\nport=5432\nscheme=arbeitszeiten_db\ndebug=True" > .env
```

**CRITICAL**: The database URI format is `postgresql://uname.db:password@host:port/scheme`. Leave `db` field empty for simple usernames.

### Build Commands

#### Frontend Build
```bash
npm run build
```
**TIMING**: Frontend build takes ~2 seconds. NEVER CANCEL. Set timeout to 30+ seconds.
**OUTPUT**: Creates `dist/data.html` from `templates/snippets/data.html`

#### Frontend Development Server
```bash
npm run dev
```
**TIMING**: Dev server starts in ~2 seconds and runs on http://localhost:1234. NEVER CANCEL.
**PURPOSE**: Live reloading development server for frontend assets with Chart.js integration.

#### Flask Application
```bash
source venv/bin/activate
python main.py
```
**TIMING**: Flask app starts in ~5 seconds and runs on http://0.0.0.0:8080. NEVER CANCEL. Set timeout to 60+ seconds.
**CRITICAL**: Requires PostgreSQL database to be running and properly configured. App will fail if database connection fails.

### No Testing Infrastructure
This repository has NO unit tests, linting tools, or automated testing. There are no pytest, flake8, black, or other testing tools configured.

## Validation Scenarios

### ALWAYS Test These Scenarios After Changes:

1. **Database Connection Test**:
   ```bash
   source venv/bin/activate
   python -c "from main import app, db; app.app_context().create_all(); print('Database connection successful')"
   ```

2. **Flask Application Startup**:
   ```bash
   source venv/bin/activate
   python main.py &
   sleep 5
   curl -s -I http://localhost:8080/ | head -1
   # Should return: HTTP/1.1 200 OK or HTTP/1.1 302 Found
   ```

3. **Frontend Build Test**:
   ```bash
   npm run build
   ls -la dist/data.html  # Should exist and be > 500 bytes
   ```

4. **Frontend Dev Server Test**:
   ```bash
   npm run dev &
   sleep 3
   curl -s -I http://localhost:1234/ | head -1
   # Should return: HTTP/1.1 200 OK
   ```

### Manual UI Testing (When Possible)
- Navigate to http://localhost:8080/ to test Flask app
- Test user registration and login flows
- Verify time tracking functionality
- Navigate to http://localhost:1234/ to test Chart.js visualization

## Key Projects and Structure

### Backend (Flask)
- **main.py**: Primary Flask application with routes
- **models.py**: SQLAlchemy database models (users, data, category, token)
- **login.py**: Authentication and user management
- **api.py**: REST API blueprint setup
- **api_resources/**: REST API endpoints for data manipulation
- **constants.py**: Application constants

### Frontend
- **templates/**: Jinja2 HTML templates
- **templates/snippets/data.html**: Chart.js data visualization page
- **static/**: CSS, JavaScript, and image assets
- **package.json**: Parcel bundler configuration

### Database Models
- **users**: User accounts with username/password
- **data**: Time tracking entries with date, hours, and categories
- **category**: User-defined work categories
- **token**: Session management tokens

## Common Gotchas

1. **Database URI Format**: Uses unusual format `postgresql://uname.db:password@host:port/scheme` - the `.db` part can be empty.

2. **Environment File**: Application reads `.env` file manually, not using python-dotenv automatically.

3. **No Tests**: Repository has no testing infrastructure. Always manually validate changes.

4. **PostgreSQL Required**: Flask app cannot run without PostgreSQL connection. Set up database first.

5. **Frontend Assets**: npm scripts build Chart.js visualizations, separate from Flask templates.

6. **Session Management**: Uses custom token-based session management, not Flask sessions.

## File Operations
- Always create backups before modifying core files (main.py, models.py)
- Check .gitignore includes: node_modules, .parcel-cache, dist, venv, .env
- Frontend changes require npm run build to take effect

## Timeout Guidelines
- **NEVER CANCEL** any build or install operations
- Python pip install: Set timeout to 300+ seconds
- npm install: Set timeout to 60+ seconds  
- npm run build: Set timeout to 30+ seconds
- Flask startup: Set timeout to 60+ seconds
- Database operations: Set timeout to 30+ seconds

Remember: This application requires both PostgreSQL database AND frontend build steps to function correctly. Always test both backend and frontend components after making changes.