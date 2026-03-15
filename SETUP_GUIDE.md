# AegisDevOps Backend Setup Guide

## Overview
This is the backend repository for **AegisDevOps**, a self-healing autonomous DevOps agent that monitors logs, detects failures, and triggers remediation actions.

The backend provides:
- **REST API endpoints** for system status and operations
- **Stress test capability** to simulate high-load scenarios
- **Error injection endpoints** for testing Aegis agent responses
- **Docker containerization** for AWS ECS deployment
- **GitHub Actions** for CI/CD (build, test, push to ECR)

---

## Local Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_ORG/aegis-devops-backend.git
cd aegis-devops-backend
```

### 2. Create Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install pytest requests  # For testing
```

### 4. Run the Application
```bash
python app.py
```
The server starts on `http://localhost:5000`

---

## API Endpoints

### Health & Status

#### `GET /health`
Basic health check
```bash
curl http://localhost:5000/health
```
Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-14T10:30:00.000000",
  "version": "1.0.0"
}
```

#### `GET /status`
Detailed system status with alerts
```bash
curl http://localhost:5000/status
```
Response includes:
- CPU usage percentage
- Memory usage and availability
- Disk usage
- Active injected errors
- Alert messages for Aegis agents

---

### Stress Testing

#### `POST /stress-test`
Trigger high-load stress test
```bash
curl -X POST http://localhost:5000/stress-test \
  -H "Content-Type: application/json" \
  -d '{"duration": 30, "concurrency": 100}'
```

Parameters:
- `duration`: How long to run the test (seconds)
- `concurrency`: Number of concurrent threads

Expected behavior:
- CPU usage increases significantly
- Memory usage increases
- Aegis monitors CloudWatch logs and detects the high load
- AWS Agent scales up ECS instances

---

### Error Injection (Testing Aegis Responses)

#### Inject Memory Leak
```bash
curl -X POST http://localhost:5000/inject-error/memory_leak
```
→ **Aegis Response**: Restart service or scale up instances

#### Inject Dependency Error
```bash
curl -X POST http://localhost:5000/inject-error/dependency_missing
```
→ **Aegis Response**: Rebuild Docker image with updated dependencies, redeploy

#### Inject Connection Timeout
```bash
curl -X POST http://localhost:5000/inject-error/connection_timeout
```
→ **Aegis Response**: Restart database connection or failover

#### Inject Out-of-Memory Error
```bash
curl -X POST http://localhost:5000/inject-error/out_of_memory
```
→ **Aegis Response**: Terminate process, restart, or scale up

#### Clear All Errors
```bash
curl -X POST http://localhost:5000/clear-error/all
```

---

### Application Routes

#### `POST /api/process`
Generic request processing endpoint (demonstrates error handling)
```bash
curl -X POST http://localhost:5000/api/process \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

---

## Docker Setup

### Build Docker Image
```bash
docker build -t aegis-devops-backend:latest .
```

### Run Docker Container Locally
```bash
docker run -p 5000:5000 \
  -e PORT=5000 \
  aegis-devops-backend:latest
```

### Health Check
The Docker image includes a health check:
```bash
docker ps  # See STATUS column for health
```

---

## GitHub Actions CI/CD Pipeline

### 1. Build and Push to AWS ECR (`build-push-ecr.yml`)

**Triggered on:**
- Push to `main` or `develop` branches
- Manual workflow dispatch

**Steps:**
1. Checkout code
2. Set up Docker Buildx
3. Configure AWS credentials (via OIDC or static keys)
4. Login to AWS ECR
5. Build Docker image
6. Push to ECR with two tags: `latest` and `{commit-sha}`
7. Run tests on built image
8. Notify deployment

**Required GitHub Secrets:**
```
AWS_ACCESS_KEY_ID          # AWS access key
AWS_SECRET_ACCESS_KEY      # AWS secret key
# OR for OIDC (recommended):
AWS_ROLE_TO_ASSUME         # IAM role ARN for OIDC
```

**Alternative: AWS_REGION**
Set the environment variable or add to GitHub secrets

### 2. Stress Test on Deployment (`stress-test.yml`)

**Triggered on:**
- Successful completion of "Build and Push to ECR" workflow
- Manual workflow dispatch

**Steps:**
1. Start Flask application
2. Run `/stress-test` endpoint with high concurrency
3. Monitor CPU and memory during test
4. Inject errors and verify detection
5. Generate test report

**Output:**
- Real-time stress test metrics
- Error scenario validation
- CloudWatch integration ready

---

## Setting Up GitHub Actions with AWS

### Option 1: Using AWS Access Keys (Simpler for Hackathon)

1. **Create AWS IAM User** with ECR permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:CreateRepository"
      ],
      "Resource": "*"
    }
  ]
}
```

2. **Generate Access Key** from AWS IAM console

3. **Add to GitHub Secrets**:
   - Go to Repository → Settings → Secrets and variables → Actions
   - Add:
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`
     - `AWS_REGION` (e.g., `us-east-1`)

4. **Uncomment the static credential line** in `.github/workflows/build-push-ecr.yml`

### Option 2: Using OIDC (More Secure, Recommended)

See AWS documentation: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect

---

## AWS ECR Setup

### Create ECR Repository
```bash
aws ecr create-repository \
  --repository-name aegis-devops-backend \
  --region us-east-1
```

### View Repository URI
```bash
aws ecr describe-repositories \
  --repository-names aegis-devops-backend \
  --region us-east-1 \
  --query 'repositories[0].repositoryUri' \
  --output text
```

Expected output: `123456789.dkr.ecr.us-east-1.amazonaws.com/aegis-devops-backend`

---

## AWS ECS Integration (For Aegis AWS Agent)

### Create ECS Task Definition
```bash
aws ecs register-task-definition \
  --family aegis-devops-backend \
  --container-definitions file://task-definition.json \
  --region us-east-1
```

Example `task-definition.json`:
```json
{
  "family": "aegis-devops-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "aegis-backend",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/aegis-devops-backend:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/aegis-devops",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

### Create ECS Service
```bash
aws ecs create-service \
  --cluster aegis-cluster \
  --service-name aegis-backend-service \
  --task-definition aegis-devops-backend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration awsvpcConfiguration='{subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}' \
  --region us-east-1
```

---

## Testing Locally

### Run Unit Tests
```bash
pip install pytest requests
python -m pytest test_stress.py -v
```

### Manual Stress Test
```bash
python -c "
import requests
import time

# Start stress test
resp = requests.post('http://localhost:5000/stress-test', 
                     json={'duration': 5, 'concurrency': 20})
print('Stress test started')

# Monitor
for i in range(6):
    status = requests.get('http://localhost:5000/status').json()
    cpu = status['system']['cpu_usage_percent']
    mem = status['system']['memory_usage_percent']
    print(f'Interval {i}: CPU {cpu}% | Memory {mem}%')
    time.sleep(1)
"
```

---

## Demo Flow (for Pitch to Judges)

### 1. Show Backend Running
```bash
curl http://localhost:5000/health
```

### 2. Trigger Stress Test
```bash
curl -X POST http://localhost:5000/stress-test \
  -H "Content-Type: application/json" \
  -d '{"duration": 30, "concurrency": 100}'
```

### 3. Show Status with Alerts
```bash
curl http://localhost:5000/status
```

### 4. Show CloudWatch Logs (AWS side)
- High CPU/Memory detected
- Aegis orchestrator routes to AWS Agent
- AWS Agent scales ECS services

### 5. Show GitHub Actions Running
- New Docker image being built
- Image pushed to ECR
- Stress tests running in CI/CD

### 6. Inject Error and Show Recovery
```bash
# Inject error
curl -X POST http://localhost:5000/inject-error/dependency_missing

# Aegis GitHub Agent detects, redockerizes, redeploys
# Show GitHub Actions logs
```

---

## Troubleshooting

### Port Already in Use
```bash
lsof -i :5000
kill -9 <PID>
```

### Docker Build Fails
```bash
docker build --no-cache -t aegis-devops-backend:latest .
```

### GitHub Actions Fails
Check logs in:
- Repository → Actions → Select workflow run → Select job
- Common issues:
  - AWS credentials not set
  - ECR repository doesn't exist
  - Docker buildx not configured

### Test Timeouts
Increase timeout in `test_stress.py` or reduce stress parameters

---

## Production Deployment Checklist

- [ ] ECR repository created
- [ ] ECS cluster and service created
- [ ] CloudWatch log groups configured
- [ ] GitHub secrets configured (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- [ ] SNS topics configured for error notifications
- [ ] Load balancer configured for ECS service
- [ ] Auto-scaling policies configured
- [ ] Aegis agents deployed and connected

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5000` | Server port |
| `FLASK_APP` | `app.py` | Flask app file |
| `PYTHONUNBUFFERED` | `1` | Real-time logging |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Repository                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │  app.py (Flask backend with error injection)     │   │
│  │  Dockerfile (Multi-stage build)                  │   │
│  │  requirements.txt                                 │   │
│  │  test_stress.py (Test suite)                     │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│            GitHub Actions (CI/CD Pipeline)               │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 1. Build Docker image                            │   │
│  │ 2. Run tests                                     │   │
│  │ 3. Push to AWS ECR                              │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│               AWS Infrastructure                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ ECR Registry │  │  ECS Service │  │  CloudWatch  │  │
│  │ (Stores      │  │  (Runs Tasks)│  │  (Logs)      │  │
│  │  Image)      │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│          Aegis Agents (Orchestrator, AWS, GitHub)       │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 1. Monitor CloudWatch logs                       │   │
│  │ 2. Detect errors via Moorcheh memory             │   │
│  │ 3. Route to appropriate agent                    │   │
│  │ 4. Execute fixes (restart, scale, redeploy)     │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [AWS ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)

---

## Support

For issues or questions, contact the team or open a GitHub issue.

**Team Members:**
- DevOps Orchestration: [Assigned]
- AWS Agent & Infrastructure: [Assigned]
- GitHub Agent & CI/CD: [You - Current]
- Moorcheh Integration: [Assigned]
