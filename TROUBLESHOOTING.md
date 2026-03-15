# Troubleshooting Guide

## Backend Issues

### "ModuleNotFoundError: No module named 'flask'"
```bash
# Solution: Install requirements
pip install -r requirements.txt

# Or if using venv:
source venv/bin/activate
pip install -r requirements.txt
```

### "Address already in use: port 5000"
```bash
# Find what's using port 5000
lsof -i :5000

# Kill the process (replace PID)
kill -9 <PID>

# Or use a different port
PORT=5001 python app.py
```

### "No module named app"
```bash
# Make sure you're in the correct directory
cd /Users/rishabnayak/genAI26dum

# Check that app.py exists
ls -la app.py

# Try again
python app.py
```

### Backend starts but no response
```bash
# Make sure it's listening
netstat -tuln | grep 5000

# Or:
curl -v http://localhost:5000/health
```

---

## Docker Issues

### "Docker: command not found"
```bash
# Install Docker Desktop on macOS:
# https://docs.docker.com/docker-for-mac/install/

# Or via Homebrew:
brew install docker
```

### "docker build" fails
```bash
# Use --no-cache to rebuild from scratch
docker build --no-cache -t aegis-backend:latest .

# Or check logs more carefully
docker build -t aegis-backend:latest . 2>&1 | tee build.log
```

### "denied: User is not authorized to access"
```bash
# Docker daemon might not be running
# Open Docker Desktop application (macOS)
# Or start Docker service (Linux)

sudo systemctl start docker
```

---

## Testing Issues

### "ConnectionError: HTTPConnectionPool"
```bash
# Make sure backend is running
python app.py

# Then in another terminal:
pytest test_stress.py -v
```

### "Request timed out"
```bash
# Increase timeout in test_stress.py:
# Change: response = requests.get(..., timeout=5)
# To: response = requests.get(..., timeout=30)
```

### "FAILED: Memory leak test"
```bash
# The test might be system-dependent
# Run individually:
pytest test_stress.py::TestErrorInjection::test_inject_memory_leak -v

# Check system memory (might not have enough free)
free -h  # Linux
vm_stat  # macOS
```

---

## GitHub Actions Issues

### "Repository does not exist" error in workflow
```bash
# Solution 1: Create repository
aws ecr create-repository \
  --repository-name aegis-devops-backend \
  --region us-east-1

# Solution 2: Check if it exists
aws ecr describe-repositories --region us-east-1
```

### "Access Denied" error in GitHub Actions
1. Go to repo → Settings → Secrets and variables → Actions
2. Verify these exist:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
3. Check for extra spaces or typos
4. If still failing, regenerate AWS credentials:
   - AWS Console → IAM → Users → github-actions
   - Security credentials → Create new access key

### Workflow doesn't appear in Actions tab
```bash
# Workflows must be in: .github/workflows/
# Check they exist:
ls -la .github/workflows/

# Check file permissions
ls -la .github/workflows/build-push-ecr.yml
```

### Docker image won't push to ECR
1. Check AWS credentials are correct
2. Verify ECR repository exists: `aws ecr describe-repositories`
3. Check region is correct: `AWS_REGION=us-east-1`
4. Try logging in manually:
   ```bash
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin YOUR_AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
   ```

---

## Git/GitHub Issues

### "fatal: not a git repository"
```bash
# Initialize git repo if needed
git init

# Add GitHub remote
git remote add origin https://github.com/YOUR_ORG/aegis-devops-backend.git

# Or check existing remote
git remote -v
```

### "Permission denied (publickey)" when pushing
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your-email@example.com"

# Add to GitHub account:
# Settings → SSH and GPG keys → New SSH key

# Test connection
ssh -T git@github.com
```

### ".gitignore not working"
```bash
# Remove cached files
git rm -r --cached .

# Re-add everything
git add .

# Commit
git commit -m "Fix gitignore"
```

---

## AWS Issues

### "UnrecognizedClientException" error
```bash
# Your AWS credentials are invalid
# Regenerate at: AWS IAM → Users → github-actions → Security credentials

# Or check if credentials are set in GitHub Actions secrets:
# Go to: GitHub repo → Settings → Secrets and variables → Actions
```

### Can't create ECR repository
```bash
# Check AWS CLI is installed
aws --version

# Configure AWS credentials
aws configure

# Then create repository:
aws ecr create-repository \
  --repository-name aegis-devops-backend \
  --region us-east-1
```

### Can't see image in ECR after push
```bash
# Check if image actually pushed
aws ecr describe-images \
  --repository-name aegis-devops-backend \
  --region us-east-1

# Check image details
aws ecr describe-images \
  --repository-name aegis-devops-backend \
  --region us-east-1 \
  --query 'imageDetails[*].[imageTags,imagePushedAt,imageSizeInBytes]'
```

---

## Performance Issues

### High memory usage locally
```bash
# Check what's using memory
ps aux | grep python

# Kill backend process
kill -9 <PID>

# Run with less concurrency:
curl -X POST http://localhost:5000/stress-test \
  -H "Content-Type: application/json" \
  -d '{"duration": 5, "concurrency": 10}'  # Less than 100
```

### Docker build very slow
```bash
# Use build cache
docker build -t aegis-backend:latest .

# Skip cache if needed
docker build --no-cache -t aegis-backend:latest .

# Check Docker disk space
docker system df
docker system prune  # Clean up dangling images
```

### GitHub Actions timeout
```bash
# Workflows have a timeout
# Increase in .github/workflows/build-push-ecr.yml:
timeout-minutes: 30  # Default is usually 360

# Or optimize Dockerfile to build faster
```

---

## Quick Diagnostics

### Backend Health Check
```bash
# Is it running?
ps aux | grep "python app.py"

# Does it respond?
curl http://localhost:5000/health

# Check the logs
tail -f app.log  # If logging to file
```

### Docker Health Check
```bash
# Is Docker running?
docker ps

# Is image built?
docker images | grep aegis

# Are there stopped containers?
docker ps -a | grep aegis
```

### GitHub Actions Health Check
```bash
# Are secrets set?
# Go to: Settings → Secrets and variables → Actions

# Did the workflow file change get committed?
git log --name-status | grep .github/workflows/

# Check workflow syntax
# Online tool: https://www.yamllint.com/
```

### AWS Health Check
```bash
# Are credentials valid?
aws sts get-caller-identity

# Does ECR repo exist?
aws ecr describe-repositories --region us-east-1

# Can we connect to ECR?
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
```

---

## Getting Help

1. **Check the error message** - Usually tells you exactly what's wrong
2. **Read the logs** - GitHub Actions shows detailed logs
3. **See SETUP_GUIDE.md** - Most common issues are covered
4. **Check app.py comments** - Code is well-documented
5. **Ask the team** - Coordinate with AWS and Orchestrator teams

---

## Common Errors & Solutions Quick Reference

| Error | Solution |
|-------|----------|
| Port already in use | `kill -9 <PID>` or `PORT=5001 python app.py` |
| Module not found | `pip install -r requirements.txt` |
| Docker build fails | `docker build --no-cache .` |
| GitHub Actions fails | Check Settings → Secrets |
| ECR not found | `aws ecr create-repository ...` |
| Access denied AWS | Regenerate AWS credentials |
| Docker: command not found | Install Docker Desktop |
| git: command not found | Install Git |
| Python: command not found | Use `python3` instead of `python` |
| Timeout in tests | Increase timeout value |

---

## When All Else Fails

```bash
# Start from scratch
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

# Or with Docker
docker system prune -a  # WARNING: Removes all images
docker build -t aegis-backend:latest .
docker run -p 5000:5000 aegis-backend:latest
```

---

**Still stuck? Open a GitHub issue or ask your team! 🚀**
