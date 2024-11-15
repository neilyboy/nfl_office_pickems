# NFL Pick'ems Application

A full-stack web application for NFL game predictions and pick'em competitions.

## Features

- User authentication and authorization with role-based access control
- Weekly NFL game picks with automated scoring
- Real-time leaderboard tracking
- Admin dashboard for game and user management
- Automatic game updates via ESPN API
- Comprehensive logging system with rotation
- Docker-based deployment for both development and production
- Secure session management with rate limiting

## Technology Stack

### Backend
- Python 3.11
- Flask (Web Framework)
- SQLite (Database)
- Flask-Login (Authentication)
- Flask-Bcrypt (Password Hashing)
- APScheduler (Task Scheduling)
- Gunicorn (WSGI Server)

### Frontend
- React
- React Router
- Axios
- Material-UI

### Infrastructure
- Docker & Docker Compose
- Nginx (Production Reverse Proxy)
- Rotating Logs
- SQLite with backup support

## Prerequisites

- Docker and Docker Compose
- Git
- Python 3.11+ (for local development)
- Node.js 16+ (for local frontend development)
- Make (optional, for using Makefile commands)

## Environment Setup

### Required Environment Variables

The repository includes a `.env.example` file with all the required environment variables. Copy this file to create your own `.env`:

```env
# Application Settings
FLASK_ENV=production  # or development
FLASK_APP=app
SECRET_KEY=your_secure_secret_key_here

# Database Settings
DATABASE_URL=sqlite:///data/nfl_pickems.db

# Logging Configuration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Security Settings
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
REMEMBER_COOKIE_SECURE=True
REMEMBER_COOKIE_HTTPONLY=True

# Rate Limiting
MAX_LOGIN_ATTEMPTS=5
LOGIN_ATTEMPT_TIMEOUT=300  # seconds

# API Configuration
REACT_APP_API_URL=http://localhost:5000
```

## Quick Start (Docker)

The fastest way to get the application running:

```bash
# Clone the repository
git clone https://github.com/neilyboy/nfl_office_pickems.git
cd nfl_office_pickems

# Create environment file
cp .env.example .env
# Edit .env with your settings

# Start the application
docker-compose up -d

# The application will be available at:
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000
```

## Directory Structure

```
.
├── app/                    # Application code
│   ├── backend/           # Flask backend
│   └── frontend/          # React frontend
├── data/                  # Database and persistent data
├── logs/                  # Application logs
├── docker-compose.yml     # Docker composition
├── Dockerfile.backend     # Backend container definition
├── Dockerfile.frontend    # Frontend container definition
├── requirements.txt       # Python dependencies
└── .env.example          # Environment template
```

## Deployment Prerequisites

Before deploying, ensure you have:

1. Docker and Docker Compose installed
2. Git installed
3. Proper network access for ports 3000 and 5000
4. At least 1GB of free disk space
5. Copy of `.env.example` to `.env` with your configuration

Common deployment issues:
- If the frontend can't connect to the backend, check REACT_APP_API_URL in your .env
- If you see database errors, ensure the data directory is writable
- For permission issues, check that the directories data/ and logs/ exist and are writable

## Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/neilyboy/nfl_office_pickems.git
cd nfl_office_pickems
```

2. Set up the backend:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your development settings

# Initialize the database
flask db upgrade

# Run development server
flask run
```

3. Set up the frontend:
```bash
cd app/frontend
npm install
npm start
```

## Production Deployment

### Using Docker (Recommended)

1. System Requirements:
   - Ubuntu 20.04 or later
   - 2GB RAM minimum
   - 10GB storage minimum

2. Install Dependencies:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker

# Add your user to docker group (optional)
sudo usermod -aG docker $USER
```

3. Application Setup:
```bash
# Clone repository
git clone https://github.com/neilyboy/nfl_office_pickems.git
cd nfl_office_pickems

# Create necessary directories
mkdir -p data logs

# Set up environment
cp .env.example .env
# Edit .env with your production settings

# Build and start containers
docker-compose up -d --build
```

4. Verify Deployment:
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f
```

### Manual Deployment (Alternative)

1. System setup:
```bash
# Install Python 3.11
sudo apt install python3.11 python3.11-venv

# Install Node.js 16
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs

# Install Nginx
sudo apt install nginx
```

2. Application setup:
```bash
# Clone and setup
git clone https://github.com/neilyboy/nfl_office_pickems.git
cd nfl_office_pickems

# Backend setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Frontend setup
cd app/frontend
npm install
npm run build
```

3. Configure Nginx:
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring and Health Checks

The application includes built-in health check endpoints and monitoring capabilities:

```bash
# Check application status
curl http://localhost:5000/health

# Monitor system resources
docker stats nfl-pickems-backend nfl-pickems-frontend
```

Key monitoring endpoints:
- `/health` - Overall application health
- `/metrics` - Application metrics (when enabled)
- `/status` - Detailed system status

## Backup and Recovery

Regular backups are essential for data safety:

1. **Automated Backups:**
   ```bash
   # Daily backups (configured in cron)
   0 0 * * * /path/to/backup_script.sh
   ```

2. **Manual Backups:**
   ```bash
   # Create a full backup
   docker-compose exec backend flask db-backup create

   # List available backups
   docker-compose exec backend flask db-backup list
   ```

3. **Recovery Procedures:**
   ```bash
   # Restore from latest backup
   docker-compose exec backend flask db-backup restore latest

   # Restore from specific backup
   docker-compose exec backend flask db-backup restore <backup_name>
   ```

## Maintenance and Operations

### Database Management

```bash
# Create backup
docker-compose exec backend python -c "from app.utils import DatabaseManager; DatabaseManager.create_backup()"

# Restore from backup
docker-compose exec backend python -c "from app.utils import DatabaseManager; DatabaseManager.restore_backup('backup_filename.sql')"
```

### Log Management

```bash
# View application logs
tail -f logs/nfl_pickems.log

# View authentication logs
tail -f logs/auth.log

# View Docker container logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Updates and Maintenance

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart containers
docker-compose down
docker-compose up -d --build

# Update dependencies
docker-compose exec backend pip install -r requirements.txt --upgrade
```

## Security Features

- **Authentication:**
  - Bcrypt password hashing with per-user salt
  - Rate limiting on login attempts
  - Session timeout and secure cookie configuration
  - HTTP-only cookies with secure flag

- **Authorization:**
  - Role-based access control
  - Fine-grained permissions system
  - Protected API endpoints

- **Infrastructure:**
  - Non-root user in Docker containers
  - Regular security updates
  - Separated development and production configurations
  - Comprehensive logging for security events

## Troubleshooting

Common issues and solutions:

1. **Database Errors:**
   - Check file permissions in data directory
   - Verify DATABASE_URL in .env
   - Ensure migrations are up to date

2. **Docker Issues:**
   - Clear Docker cache: `docker system prune -a`
   - Check logs: `docker-compose logs`
   - Verify network connectivity

3. **Authentication Problems:**
   - Check SECRET_KEY configuration
   - Verify cookie settings in .env
   - Review auth.log for specific errors

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and feature requests, please use the GitHub issue tracker.
