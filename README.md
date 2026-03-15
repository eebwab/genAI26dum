# AegisDevOps Backend

**A self-healing autonomous DevOps agent that monitors logs, detects failures, and executes remediation actions.**

This repository contains the **backend service** that generates failure scenarios and provides APIs for the Aegis orchestrator to monitor and remediate.

---

## 🎯 Project Overview

**AegisDevOps** bridges the gap between "hackathon prototype" and "production-ready tool" by combining:
- **Moorcheh**: High-efficiency information-theoretic memory for pattern recognition
- **Railtracks**: Orchestration engine for multi-agent workflows
- **This Backend**: Test scenarios and monitoring APIs

---

## 📋 Quick Start

### Local Development (5 min)
```bash
# Clone and setup
git clone <repo-url>
cd aegis-devops-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

Server runs on `http://localhost:5000`

### Docker (2 min)
```bash
# Build
docker build -t aegis-backend:latest .

# Run
docker run -p 5000:5000 aegis-backend:latest

# Or use docker-compose
docker-compose up
```

---

## 🚀 Core Features

### 1. **Stress Test Endpoint** - Trigger High-Load Scenarios
```bash
curl -X POST http://localhost:5000/stress-test \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 30,      # Run for 30 seconds
    "concurrency": 100   # 100 concurrent threads
  }'
```

**Result**: CPU/Memory spike detected by Aegis → AWS Agent scales up ECS

### 2. **Error Injection** - Simulate Real Failures
```bash
# Memory leak
curl -X POST http://localhost:5000/inject-error/memory_leak

# Dependency error
curl -X POST http://localhost:5000/inject-error/dependency_missing

# Connection timeout
curl -X POST http://localhost:5000/inject-error/connection_timeout

# Out of memory
curl -X POST http://localhost:5000/inject-error/out_of_memory
```

**Result**: Aegis routes to appropriate agent:
- **AWS Agent**: Restart/scale instances
- **GitHub Agent**: Rebuild Docker image, redeploy

### 3. **Real-Time Monitoring** - Status & Alerts
```bash
curl http://localhost:5000/status
```

Response includes:
- Current CPU/Memory/Disk usage
- Active error states
- Alert messages for Aegis agents
- Memory buffer size

### 4. **Health Checks** - For Load Balancers & Orchestrators
```bash
curl http://localhost:5000/health
```

---

## 📡 API Reference

### Health & Status

#### `GET /health`
```bash
curl http://localhost:5000/health
```
```json
{
  "status": "healthy",
  "timestamp": "2026-03-14T10:30:00.000000",
  "version": "1.0.0"
}
```

#### `GET /status`
```bash
curl http://localhost:5000/status
```
```json
{
  "timestamp": "...",
  "system": {
    "cpu_usage_percent": 75.3,
    "memory_usage_percent": 62.1,
    "memory_available_mb": 4096.5,
    "disk_usage_percent": 45.2
  },
  "application": {
    "memory_buffer_size": 1024,
    "injected_errors": {
      "memory_leak": false,
      "dependency_missing": false,
      ...
    }
  },
  "alerts": [
    {
      "severity": "HIGH",
      "message": "CPU usage critical: 95%",
      "recommendation": "Scale up ECS instances"
    }
  ]
}
```

### Stress Testing

#### `POST /stress-test`
Trigger high CPU/memory load
```bash
curl -X POST http://localhost:5000/stress-test \
  -H "Content-Type: application/json" \
  -d '{"duration": 30, "concurrency": 100}'
```

### Error Injection

#### `POST /inject-error/{error_type}`
```bash
# Types: memory_leak, dependency_missing, connection_timeout, out_of_memory
curl -X POST http://localhost:5000/inject-error/memory_leak
```

#### `POST /clear-error/{error_type}`
```bash
# Clear specific error or all
curl -X POST http://localhost:5000/clear-error/memory_leak
curl -X POST http://localhost:5000/clear-error/all
```

### Application Routes

#### `GET /memory-leak`
Endpoint that fails if memory_leak error is injected

#### `GET /missing-dependency`
Endpoint that fails if dependency_missing error is injected

#### `GET /timeout-test`
Endpoint that hangs if connection_timeout error is injected

#### `POST /api/process`
Generic endpoint for testing error handling
```bash
curl -X POST http://localhost:5000/api/process \
  -H "Content-Type: application/json" \
  -d '{"data": "test"}'
```

---

## 🧪 Testing

### Run Stress Tests
```bash
pip install pytest requests
pytest test_stress.py -v
```

### Manual Integration Test
```bash
# Start backend
python app.py &

# Run stress test
python -c "
import requests, time

# Trigger stress
requests.post('http://localhost:5000/stress-test', 
              json={'duration': 5, 'concurrency': 20})

# Monitor
for i in range(6):
    status = requests.get('http://localhost:5000/status').json()
    print(f'CPU: {status[\"system\"][\"cpu_usage_percent\"]}% | Memory: {status[\"system\"][\"memory_usage_percent\"]}%')
    time.sleep(1)
"
```

---

## 🐳 Docker & Deployment

### Build Docker Image
```bash
docker build -t aegis-devops-backend:latest .
```

### Run Locally
```bash
docker run -p 5000:5000 aegis-devops-backend:latest
```

### Health Check (in Docker)
```bash
curl -f http://localhost:5000/health || exit 1
```

### Push to AWS ECR
```bash
# Login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <AWS_ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com

# Tag
docker tag aegis-devops-backend:latest \
  <AWS_ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com/aegis-devops-backend:latest

# Push
docker push <AWS_ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com/aegis-devops-backend:latest
```

---

## 🔄 GitHub Actions CI/CD

### Workflows Included

#### 1. Build and Push to ECR (`.github/workflows/build-push-ecr.yml`)
Triggered on: `git push origin main`

**Steps:**
1. Build Docker image
2. Run tests
3. Push to AWS ECR with tags: `latest` and `{commit-sha}`
4. Ready for AWS agent to deploy

#### 2. Stress Test on Deployment (`.github/workflows/stress-test.yml`)
Triggered on: Successful ECR push

**Steps:**
1. Start Flask backend
2. Run stress test
3. Monitor metrics
4. Inject errors
5. Generate report

### Setup GitHub Actions

1. **Add AWS Credentials to GitHub Secrets**:
   - Repo → Settings → Secrets and variables → Actions
   - Add: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`

2. **Create ECR Repository**:
   ```bash
   aws ecr create-repository --repository-name aegis-devops-backend --region us-east-1
   ```

3. **Push Code**:
   ```bash
   git push origin main
   ```
   
   Watch workflow run: Repo → Actions

---

## 🎯 Demo Scenario

### What Happens When Aegis Runs

**Timeline:**
1. **T+0s**: You call `/stress-test` endpoint
2. **T+2s**: CPU jumps to 95%, Memory to 80%
3. **T+3s**: CloudWatch logs show high load
4. **T+4s**: Aegis Orchestrator detects via Moorcheh memory
5. **T+5s**: Routes to AWS Agent
6. **T+6s**: AWS Agent scales ECS from 2 → 5 instances
7. **T+10s**: Load distributed, metrics normalize

**GitHub Agent Equivalent:**
1. Error detected: "Missing dependency"
2. GitHub Agent routes: "Need Docker rebuild"
3. Pulls code, updates dependencies
4. Rebuilds Docker image
5. Pushes to ECR
6. AWS agent pulls new image and deploys

---

## 📁 Project Structure

```
aegis-devops-backend/
├── app.py                    # Main Flask application
├── Dockerfile                # Docker build config
├── docker-compose.yml        # Docker Compose for local dev
├── requirements.txt          # Python dependencies
├── test_stress.py            # Comprehensive test suite
├── .env.example              # Environment variables template
├── SETUP_GUIDE.md            # Detailed setup instructions
├── QUICK_REFERENCE.md        # Quick reference for team
├── README.md                 # This file
└── .github/
    └── workflows/
        ├── build-push-ecr.yml    # Build and push workflow
        └── stress-test.yml       # Stress test workflow
```

---

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5000` | Server port |
| `FLASK_APP` | `app.py` | Flask entry point |
| `FLASK_ENV` | `development` | Flask environment |
| `PYTHONUNBUFFERED` | `1` | Real-time logging |

---

## 📊 Metrics & Monitoring

### Key Metrics Aegis Monitors

- **CPU Usage**: Triggers scale-up above 80%
- **Memory Usage**: Triggers restart above 80%
- **Memory Buffer**: Growing indicates memory leak
- **Error Count**: Threshold for escalation
- **Response Time**: Indicates connection issues

### CloudWatch Integration

When running on AWS ECS:
- All logs → CloudWatch Logs (`/ecs/aegis-devops`)
- Aegis Orchestrator subscribes to log events
- Triggers agent workflows on error patterns

---

## 🚨 Error Scenarios

| Error Type | Symptom | Aegis Response |
|-----------|---------|----------------|
| **Memory Leak** | Memory grows unbounded | Restart service or scale up |
| **Dependency Error** | Import fails | Rebuild Docker, redeploy |
| **Connection Timeout** | DB connection fails | Restart connection pool |
| **Out of Memory** | Process killed | Scale to larger instance |
| **High Load** | CPU/Memory spike | Scale ECS instances |

---

## 🛠️ Troubleshooting

### Backend Won't Start
```bash
# Check port
lsof -i :5000

# Kill existing process
kill -9 <PID>

# Try different port
PORT=5001 python app.py
```

### Docker Build Fails
```bash
# Check Python version
python --version  # Should be 3.11+

# Rebuild without cache
docker build --no-cache .
```

### GitHub Actions Error
1. Check repo → Actions → Workflow run
2. Verify AWS credentials in Settings → Secrets
3. Confirm ECR repository exists in AWS

### Tests Timeout
- Increase timeout in `test_stress.py`
- Reduce concurrency in stress test parameters
- Check system resources

---

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)

---

## 👥 Team Roles

- **Backend & GitHub Actions** (You): Flask app, error injection, CI/CD
- **AWS Agent**: ECS scaling, service management
- **GitHub Agent**: Docker rebuild, code deployment
- **Orchestrator**: Error detection, agent routing
- **Moorcheh Integration**: Memory pattern recognition

---

## 📝 Deployment Checklist

- [ ] Backend runs locally
- [ ] Docker image builds
- [ ] GitHub Actions secrets configured
- [ ] AWS ECR repository created
- [ ] Workflows test and push successfully
- [ ] Stress test generates high metrics
- [ ] Error injection works
- [ ] Ready for Aegis agent integration

---

## 🎤 For the Demo

**Script to show judges:**

> "Most hackathon projects hardcode API wrappers. We designed AegisDevOps using Model Context Protocol standards. When the backend reports high CPU (which you see here at 95%), our Orchestrator Agent searches Moorcheh's memory for similar issues. It instantly routes to the AWS Agent, which uses MCP tools to scale ECS from 2 to 5 instances. Meanwhile, the GitHub Agent rebuilds and deploys the Docker image. This isn't scripted—it's truly autonomous reasoning with memory."

---

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: See `SETUP_GUIDE.md` and `QUICK_REFERENCE.md`
- **Questions**: Contact the team

---

**Happy Hacking! 🚀**
