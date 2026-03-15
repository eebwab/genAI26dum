# AegisDevOps GitHub & Backend Quick Reference

## Your Responsibilities (GitHub Backend & CI/CD)

### ✅ What You're Handling
1. **GitHub Repository** - Backend code with error injection endpoints
2. **GitHub Actions Workflows** - Build, test, push to AWS ECR
3. **Stress Test Suite** - Tests that Aegis can detect and respond to
4. **Docker Image** - Containerized backend for ECS deployment

### 🚀 Quick Start

#### Local Development
```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run
python app.py

# Test
pip install pytest requests
pytest test_stress.py -v
```

#### Docker Build
```bash
docker build -t aegis-devops-backend:latest .
docker run -p 5000:5000 aegis-devops-backend:latest
```

---

## API Endpoints (Your Backend)

| Endpoint | Method | Purpose | Demo Use |
|----------|--------|---------|----------|
| `/health` | GET | Basic health check | Verify app is running |
| `/status` | GET | System metrics + alerts | Show Aegis what to fix |
| `/stress-test` | POST | Trigger high load | Simulate production failure |
| `/inject-error/<type>` | POST | Inject errors | Test Aegis agent routing |
| `/clear-error/<type>` | POST | Clear injected errors | Reset for next test |

### Quick API Test
```bash
# Health
curl http://localhost:5000/health

# Status with metrics
curl http://localhost:5000/status

# Stress test (30 sec, 100 concurrent)
curl -X POST http://localhost:5000/stress-test \
  -H "Content-Type: application/json" \
  -d '{"duration": 30, "concurrency": 100}'

# Inject memory leak
curl -X POST http://localhost:5000/inject-error/memory_leak

# Clear all
curl -X POST http://localhost:5000/clear-error/all
```

---

## GitHub Actions Workflows

### 1. Build and Push to ECR (`.github/workflows/build-push-ecr.yml`)
**Triggered on:**
- Push to `main` or `develop`
- Manual trigger

**Does:**
1. Builds Docker image
2. Pushes to AWS ECR with tags: `latest` and `{commit-sha}`
3. Runs tests on built image
4. Ready for AWS agent to deploy

**GitHub Secrets Needed:**
```
AWS_ACCESS_KEY_ID          # Get from AWS IAM
AWS_SECRET_ACCESS_KEY      # Get from AWS IAM
AWS_REGION                 # e.g., us-east-1
```

### 2. Stress Test on Deployment (`.github/workflows/stress-test.yml`)
**Triggered on:**
- Successful ECR push workflow
- Manual trigger

**Does:**
1. Starts Flask backend
2. Runs `/stress-test` endpoint
3. Monitors CPU/Memory metrics
4. Injects errors and verifies detection
5. Logs results for Aegis agents

---

## Setting Up GitHub Actions with AWS

### Step 1: Create AWS IAM User
1. Go to AWS Console → IAM → Users → Create user
2. Name: `github-actions`
3. Attach policy: `AmazonEC2ContainerRegistryPowerUser`

### Step 2: Create Access Keys
1. Select user → Security credentials → Create access key
2. Choose: "Other"
3. Copy the Access Key ID and Secret Access Key

### Step 3: Add to GitHub Secrets
1. Go to repo → Settings → Secrets and variables → Actions
2. Click "New repository secret" 3 times:
   - Name: `AWS_ACCESS_KEY_ID` → Value: [paste access key]
   - Name: `AWS_SECRET_ACCESS_KEY` → Value: [paste secret key]
   - Name: `AWS_REGION` → Value: `us-east-1` (or your region)

### Step 4: Create ECR Repository
```bash
aws ecr create-repository \
  --repository-name aegis-devops-backend \
  --region us-east-1
```

### Step 5: Test the Workflow
1. Make a commit and push to `main`
2. Go to repo → Actions
3. Watch `Build and Push to AWS ECR` workflow run
4. Confirm image appears in AWS ECR

---

## Demo Flow (What to Show Judges)

### Part 1: Show Backend Running
```bash
# Terminal 1: Start backend
python app.py

# Terminal 2: Check health
curl http://localhost:5000/health
```

### Part 2: Run Stress Test
```bash
# Show status baseline
curl http://localhost:5000/status | jq '.system'

# Run stress test (will take ~30 sec)
curl -X POST http://localhost:5000/stress-test \
  -H "Content-Type: application/json" \
  -d '{"duration": 30, "concurrency": 100}'

# In another terminal, monitor during test
for i in {1..10}; do
  curl http://localhost:5000/status | jq '.system | {cpu: .cpu_usage_percent, memory: .memory_usage_percent}'
  sleep 3
done
```

### Part 3: Show GitHub Actions Building Image
1. Make a commit: `git push origin main`
2. Go to GitHub repo → Actions
3. Show workflow running:
   - Building Docker image ✓
   - Running tests ✓
   - Pushing to AWS ECR ✓

### Part 4: Show Error Scenarios
```bash
# Inject memory leak
curl -X POST http://localhost:5000/inject-error/memory_leak
curl http://localhost:5000/status | jq '.alerts'

# Inject dependency error
curl -X POST http://localhost:5000/inject-error/dependency_missing
curl http://localhost:5000/missing-dependency

# Aegis agents would see these and:
# - AWS Agent: Restart service, scale up
# - GitHub Agent: Rebuild Docker image, push to ECR, redeploy
```

---

## File Structure
```
├── app.py                           # Main Flask backend
├── Dockerfile                       # Docker build configuration
├── requirements.txt                 # Python dependencies
├── test_stress.py                   # Test suite
├── SETUP_GUIDE.md                   # Detailed setup guide
├── QUICK_REFERENCE.md               # This file
└── .github/
    └── workflows/
        ├── build-push-ecr.yml       # Build & push to ECR
        └── stress-test.yml          # Stress test workflow
```

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Port 5000 already in use | `lsof -i :5000 && kill -9 <PID>` |
| Docker build fails | `docker build --no-cache ...` |
| GitHub Actions AWS error | Check secrets in Settings → Secrets |
| ECR push fails | Verify AWS credentials and ECR repo exists |
| Tests timeout | Reduce stress parameters or increase timeout |

---

## Key Metrics for Demo

### Before Stress Test
- CPU: ~5-10%
- Memory: ~20-30%
- No alerts

### During Stress Test (What Aegis Sees)
- CPU: **80-95%**
- Memory: **70-85%**
- **Alerts**: "CPU usage critical", "Memory usage critical"
- **Log Entry**: `{"event": "STRESS_TEST_STARTED", "severity": "HIGH"}`

### Aegis Agent Response
- **Orchestrator**: Detects high load via Moorcheh memory
- **AWS Agent**: Scales ECS desired count from 2 → 5+ instances
- **Result**: More Docker containers running

---

## Handoff Checklist

- [ ] GitHub repository created and pushed
- [ ] GitHub Secrets configured (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
- [ ] AWS ECR repository created
- [ ] GitHub Actions workflows tested and working
- [ ] Docker image successfully builds and pushes to ECR
- [ ] Stress test runs and generates high CPU/memory
- [ ] Error injection endpoints working
- [ ] Backend ready for AWS agent integration

---

## Important Dates

- **Hackathon Start**: [Your date]
- **First Demo**: [Your date]
- **Final Submission**: [Your date]

---

## Contact & Questions

- **Backend Issues**: Check SETUP_GUIDE.md or GitHub Issues
- **AWS Integration**: Contact AWS Agent team
- **Orchestration**: Contact Orchestrator team
- **Memory Integration**: Contact Moorcheh team

---

## Next Steps After Setup

1. ✅ Backend running locally
2. ✅ GitHub Actions pushing to ECR
3. → AWS Agent team: Integrate with ECS
4. → Orchestrator team: Route errors to agents
5. → Moorcheh team: Store error patterns
6. → Final integration and demo

**You are responsible for #1-2 and coordinating with the AWS team on ECR.**
