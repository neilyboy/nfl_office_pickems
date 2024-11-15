$ErrorActionPreference = "Stop"

# Configuration
$remoteHost = "192.168.1.158"
$remoteUser = "neil"
$remotePath = "/home/neil/nfl-pickems-test"

Write-Host "Creating remote directory..."
# You'll be prompted for password
ssh ${remoteUser}@${remoteHost} "rm -rf $remotePath && mkdir -p $remotePath"

Write-Host "Copying project files..."
# You'll be prompted for password again
scp -r app requirements.txt pytest.ini test_data ${remoteUser}@${remoteHost}:${remotePath}/

Write-Host "Setting up Python environment and running tests..."
# You'll be prompted for password one more time
ssh ${remoteUser}@${remoteHost} "cd $remotePath && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python -m pytest app/backend/tests -v"
