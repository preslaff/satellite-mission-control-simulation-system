# Database Setup Guide

This guide explains how to set up PostgreSQL for the Satellite Mission Control Simulation System.

## Table of Contents
- [PostgreSQL Installation](#postgresql-installation)
  - [Windows](#windows)
  - [Linux (Ubuntu/Debian)](#linux-ubuntudebian)
  - [macOS](#macos)
  - [Docker](#docker)
- [Database Configuration](#database-configuration)
- [Running Migrations](#running-migrations)
- [Optional: TimescaleDB](#optional-timescaledb)
- [Troubleshooting](#troubleshooting)

## PostgreSQL Installation

### Windows

1. **Download PostgreSQL:**
   - Visit https://www.postgresql.org/download/windows/
   - Download the installer for PostgreSQL 14+ (latest recommended)

2. **Run the Installer:**
   - Execute the downloaded installer
   - Default installation directory: `C:\Program Files\PostgreSQL\<version>`
   - Set a password for the `postgres` superuser (remember this!)
   - Default port: 5432
   - Install the Stack Builder components (optional)

3. **Verify Installation:**
   ```powershell
   psql --version
   ```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify installation
psql --version
```

### macOS

```bash
# Using Homebrew
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Verify installation
psql --version
```

### Docker

The easiest way to run PostgreSQL is with Docker:

```bash
# Pull PostgreSQL image
docker pull postgres:14

# Run PostgreSQL container
docker run --name satcom-postgres \
  -e POSTGRES_USER=satcom \
  -e POSTGRES_PASSWORD=satcom \
  -e POSTGRES_DB=satcom \
  -p 5432:5432 \
  -v satcom-data:/var/lib/postgresql/data \
  -d postgres:14

# Verify container is running
docker ps | grep satcom-postgres
```

## Database Configuration

### 1. Create Database and User

**Using psql (Windows/Linux/macOS):**

```bash
# Connect to PostgreSQL as superuser
sudo -u postgres psql  # Linux/macOS
psql -U postgres       # Windows (if in PATH)

# Or specify connection details
psql -h localhost -U postgres
```

**Execute the following SQL commands:**

```sql
-- Create user
CREATE USER satcom WITH PASSWORD 'satcom';

-- Create database
CREATE DATABASE satcom OWNER satcom;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE satcom TO satcom;

-- Connect to the database
\c satcom

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO satcom;

-- Exit psql
\q
```

### 2. Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
cd backend
cp .env.example .env  # If .env.example exists
```

Edit `.env` and set:

```env
DATABASE_URL=postgresql://satcom:satcom@localhost:5432/satcom
```

**For Docker:**
```env
DATABASE_URL=postgresql://satcom:satcom@localhost:5432/satcom
```

**For custom configuration:**
```env
DATABASE_URL=postgresql://username:password@host:port/database
```

### 3. Test Database Connection

```bash
# Activate virtual environment
cd backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Test connection with Python
python -c "from app.core.database import check_db_connection; print('Connected!' if check_db_connection() else 'Failed!')"
```

## Running Migrations

### Create Initial Migration

```bash
cd backend

# Create migration
venv/Scripts/python.exe -m alembic revision --autogenerate -m "Initial migration"

# Or on Linux/macOS
python -m alembic revision --autogenerate -m "Initial migration"
```

### Apply Migrations

```bash
# Apply all pending migrations
venv/Scripts/python.exe -m alembic upgrade head

# Or on Linux/macOS
python -m alembic upgrade head
```

### Check Migration Status

```bash
# Show current revision
venv/Scripts/python.exe -m alembic current

# Show migration history
venv/Scripts/python.exe -m alembic history
```

### Rollback Migration

```bash
# Rollback one migration
venv/Scripts/python.exe -m alembic downgrade -1

# Rollback to specific revision
venv/Scripts/python.exe -m alembic downgrade <revision_id>

# Rollback all migrations
venv/Scripts/python.exe -m alembic downgrade base
```

## Optional: TimescaleDB

For better performance with time-series telemetry data, install TimescaleDB extension:

### Install TimescaleDB

**Windows:**
- Download from https://docs.timescale.com/install/latest/self-hosted/installation-windows/
- Run installer

**Linux:**
```bash
# Add TimescaleDB repository
sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -

# Install TimescaleDB
sudo apt update
sudo apt install timescaledb-2-postgresql-14

# Configure TimescaleDB
sudo timescaledb-tune
```

**Docker:**
```bash
# Use TimescaleDB image instead of postgres
docker run --name satcom-timescale \
  -e POSTGRES_USER=satcom \
  -e POSTGRES_PASSWORD=satcom \
  -e POSTGRES_DB=satcom \
  -p 5432:5432 \
  -v satcom-data:/var/lib/postgresql/data \
  -d timescale/timescaledb:latest-pg14
```

### Enable TimescaleDB Extension

#### 1. Preload TimescaleDB Library

TimescaleDB must be preloaded before you can create the extension.

**Edit postgresql.conf:**

```bash
# Windows - Open as Administrator
notepad "E:/PostgreSQL/17/data/postgresql.conf"

# Linux/macOS
sudo nano /etc/postgresql/14/main/postgresql.conf
```

**Find and modify the line:**

```ini
# Find this line (might be commented out with #)
#shared_preload_libraries = ''

# Change it to:
shared_preload_libraries = 'timescaledb'

# If other extensions are already loaded:
shared_preload_libraries = 'timescaledb,other_extension'
```

**Or append to the file (Windows PowerShell as Administrator):**

```powershell
# Backup first
Copy-Item "E:/PostgreSQL/17/data/postgresql.conf" "E:/PostgreSQL/17/data/postgresql.conf.backup"

# Add configuration
Add-Content -Path "E:/PostgreSQL/17/data/postgresql.conf" -Value "`nshared_preload_libraries = 'timescaledb'"
```

#### 2. Restart PostgreSQL

**Windows - Using Services:**
1. Press `Win + R`, type `services.msc`, press Enter
2. Find "postgresql-x64-17" (or your version)
3. Right-click → Restart

**Windows - Using PowerShell (as Administrator):**
```powershell
Restart-Service -Name "postgresql-x64-17"
```

**Linux/macOS:**
```bash
sudo systemctl restart postgresql
```

**Docker:**
```bash
docker restart satcom-timescale
```

#### 3. Create TimescaleDB Extension

```sql
-- Connect to database
psql -U satcom -d satcom

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Verify it's installed
\dx

-- You should see timescaledb in the list
```

#### 4. Important: Telemetry Table Requirements

**The telemetry table uses a composite primary key to support TimescaleDB:**

The model is configured with:
```python
id = Column(Integer, primary_key=True)
satellite_id = Column(Integer, ForeignKey("satellites.id"), primary_key=True)
timestamp = Column(DateTime(timezone=True), primary_key=True)
```

This composite primary key `(id, satellite_id, timestamp)` is **required** for TimescaleDB hypertables.

**If you already created the table without the composite key:**

```sql
-- Drop the existing table
DROP TABLE IF EXISTS telemetry CASCADE;

-- Recreate with correct schema via Alembic
-- (Run this in your terminal, not psql)
```

Then in your terminal:
```bash
cd backend
venv/Scripts/python.exe -m alembic upgrade head
```

#### 5. Convert to Hypertable

After the table is created with the correct schema:

```sql
-- Connect to database
psql -U satcom -d satcom

-- Convert telemetry table to hypertable
SELECT create_hypertable('telemetry', 'timestamp');

-- Verify the hypertable was created
SELECT * FROM timescaledb_information.hypertables;

-- You should see telemetry listed
```

#### 6. Optional: Add Data Retention Policy

Automatically delete old telemetry data:

```sql
-- Keep data for 1 year
SELECT add_retention_policy('telemetry', INTERVAL '1 year');

-- Or keep data for 90 days
SELECT add_retention_policy('telemetry', INTERVAL '90 days');

-- Check retention policies
SELECT * FROM timescaledb_information.jobs WHERE proc_name = 'policy_retention';
```

#### 7. Optional: Add Compression Policy

Compress old data to save space:

```sql
-- Enable compression on the hypertable
ALTER TABLE telemetry SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'satellite_id'
);

-- Compress data older than 7 days
SELECT add_compression_policy('telemetry', INTERVAL '7 days');

-- Check compression policies
SELECT * FROM timescaledb_information.jobs WHERE proc_name = 'policy_compression';

-- View compression stats
SELECT * FROM timescaledb_information.compressed_chunk_stats;
```

#### 8. Verify Setup

```sql
-- Check table structure
\d telemetry

-- Should show:
-- Composite primary key: (id, satellite_id, timestamp)
-- Hypertable: Yes

-- Test insert
INSERT INTO telemetry (id, satellite_id, timestamp, position_x, position_y, position_z, velocity_x, velocity_y, velocity_z)
VALUES (1, 1, NOW(), 1000.0, 2000.0, 3000.0, 7.5, 0.5, 0.5);

-- Query should work
SELECT * FROM telemetry WHERE satellite_id = 1;
```

## Troubleshooting

### Connection Refused Error

**Error:** `connection to server at "localhost" (127.0.0.1), port 5432 failed`

**Solutions:**
1. Check if PostgreSQL is running:
   ```bash
   # Windows
   Get-Service postgresql*

   # Linux/macOS
   sudo systemctl status postgresql

   # Docker
   docker ps | grep postgres
   ```

2. Start PostgreSQL service:
   ```bash
   # Windows
   Start-Service postgresql-x64-14

   # Linux/macOS
   sudo systemctl start postgresql

   # Docker
   docker start satcom-postgres
   ```

### Authentication Failed Error

**Error:** `password authentication failed for user "satcom"`

**Solutions:**
1. Check credentials in `.env` match database user
2. Recreate user with correct password:
   ```sql
   DROP USER IF EXISTS satcom;
   CREATE USER satcom WITH PASSWORD 'satcom';
   GRANT ALL PRIVILEGES ON DATABASE satcom TO satcom;
   ```

### Permission Denied Error

**Error:** `permission denied for schema public`

**Solution:**
```sql
-- Connect as superuser
psql -U postgres -d satcom

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO satcom;
GRANT ALL ON ALL TABLES IN SCHEMA public TO satcom;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO satcom;
```

### Port Already in Use

**Error:** `port 5432 is already in use`

**Solutions:**
1. Change PostgreSQL port in `postgresql.conf`
2. Use different port in DATABASE_URL:
   ```env
   DATABASE_URL=postgresql://satcom:satcom@localhost:5433/satcom
   ```
3. Stop other PostgreSQL instances

### Alembic Migration Errors

**Error:** `Target database is not up to date`

**Solution:**
```bash
# Check current version
venv/Scripts/python.exe -m alembic current

# Apply all migrations
venv/Scripts/python.exe -m alembic upgrade head
```

### TimescaleDB Errors

#### Error: extension "timescaledb" must be preloaded

**Full Error:**
```
FATAL: extension "timescaledb" must be preloaded
HINT: Please preload the timescaledb library via shared_preload_libraries.
```

**Solution:**
1. Edit `postgresql.conf` and add `shared_preload_libraries = 'timescaledb'`
2. Restart PostgreSQL service
3. Try creating the extension again

See [Enable TimescaleDB Extension](#enable-timescaledb-extension) section above for detailed steps.

#### Error: cannot create a unique index without the column "timestamp"

**Full Error:**
```
ERROR: cannot create a unique index without the column "timestamp" (used in partitioning)
HINT: If you're creating a hypertable on a table with a primary key, ensure the partitioning column is part of the primary or composite key.
```

**Cause:** The telemetry table was created without `timestamp` in the primary key.

**Solution:**
```sql
-- Drop the existing table
DROP TABLE IF EXISTS telemetry CASCADE;
```

Then recreate with the correct schema:
```bash
cd backend
venv/Scripts/python.exe -m alembic upgrade head
```

The new schema includes a composite primary key: `(id, satellite_id, timestamp)`

#### Error: SQLAlchemy 2.0 "Textual SQL expression should be explicitly declared"

**Full Error:**
```
Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')
```

**Solution:** Already fixed in the codebase. Update to latest version:
```bash
git pull origin master
```

The fix wraps raw SQL in `text()`:
```python
from sqlalchemy import text
db.execute(text('SELECT 1'))
```

## Verify Setup

Run the backend server and check the health endpoint:

```bash
# Start backend
cd backend
venv/Scripts/python.exe -m uvicorn app.main:app --reload

# Check health endpoint (in another terminal)
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "api": "operational",
    "database": "operational",
    "ml_models": "pending"
  }
}
```

## Next Steps

After successful database setup:

1. The application will automatically create tables on first run (if `init_db()` is uncommented in `main.py`)
2. Or manually run migrations: `alembic upgrade head`
3. Start populating satellite data via the API
4. Configure ground stations
5. Enable telemetry collection

For production deployment, consider:
- Using connection pooling (already configured with SQLAlchemy)
- Setting up database backups
- Configuring TimescaleDB for time-series data
- Implementing read replicas for scaling
- Using managed PostgreSQL services (AWS RDS, Google Cloud SQL, etc.)
