# GitHub Actions Setup for AWS ECR

## Step-by-Step Guide: Getting GitHub Actions to Push to AWS ECR

### Phase 1: AWS Setup (10 minutes)

#### 1.1 Create IAM User for GitHub
Go to AWS Console:
1. **Services** → **IAM** → **Users** → **Create user**
2. **Username**: `github-actions`
3. **Console access**: Uncheck
4. Click **Create user**

#### 1.2 Attach ECR Permissions
1. Click on the user you created
2. **Add permissions** → **Attach policies directly**
3. Search for: `AmazonEC2ContainerRegistryPowerUser`
4. ✓ Check it
5. **Add permissions**

#### 1.3 Create Access Key
1. In the user, go to **Security credentials**
2. **Create access key**
3. Choose: **Other**
4. **Create access key**
5. **Copy** both:
   - **Access Key ID**
   - **Secret Access Key**
   - (You'll need these in Step 2)

#### 1.4 Create ECR Repository
In AWS Console (or terminal):
```bash
aws ecr create-repository \
  --repository-name aegis-devops-backend \
  --region us-east-1
```

Get the repository URI:
```bash
aws ecr describe-repositories \
  --repository-names aegis-devops-backend \
  --region us-east-1 \
  --query 'repositories[0].repositoryUri' \
  --output text
```

Example output: `123456789012.dkr.ecr.us-east-1.amazonaws.com/aegis-devops-backend`

---

### Phase 2: GitHub Setup (5 minutes)

#### 2.1 Add GitHub Secrets
1. Go to your **GitHub Repository**
2. Click **Settings** (top right)
3. Left sidebar → **Secrets and variables** → **Actions**
4. Click **New repository secret** (green button)

**Add 3 secrets:**

**Secret 1:**
- Name: `AWS_ACCESS_KEY_ID`
- Value: [Paste from 1.3]
- Click **Add secret**

**Secret 2:**
- Name: `AWS_SECRET_ACCESS_KEY`
- Value: [Paste from 1.3]
- Click **Add secret**

**Secret 3:**
- Name: `AWS_REGION`
- Value: `us-east-1`
- Click **Add secret**

**Result:** You should see 3 secrets listed

---

### Phase 3: Test the Workflow (5 minutes)

#### 3.1 Trigger Workflow Manually
1. Go to **Actions** tab
2. Click **Build and Push to AWS ECR** workflow
3. Click **Run workflow**
4. Select branch: `main`
5. Click **Run workflow**

#### 3.2 Watch It Build
1. Click the workflow run
2. Click **build-and-push** job
3. Watch the steps execute:
   - ✓ Checkout code
   - ✓ Set up Docker Buildx
   - ✓ Configure AWS credentials
   - ✓ Login to Amazon ECR
   - ✓ Build Docker image
   - ✓ Push image to Amazon ECR
   - ✓ Output image URI

#### 3.3 Verify in AWS
```bash
# List ECR images
aws ecr describe-images \
  --repository-name aegis-devops-backend \
  --region us-east-1
```

You should see your image!

---

### Phase 4: Automate on Push (Setup Once)

After Phase 3 works, the workflow automatically runs when you:
```bash
git add .
git commit -m "Deploy aegis backend"
git push origin main
```

Or push to `develop` branch - it also triggers!

---

## Workflow Files Explained

### `.github/workflows/build-push-ecr.yml`
**What it does:**
1. Builds Docker image with your code
2. Pushes to AWS ECR with 2 tags:
   - `latest` - always points to newest
   - `{commit-sha}` - specific version
3. Runs tests on the built image
4. Creates a notification when done

**Triggered by:**
- Push to `main` or `develop`
- Manual trigger (Run workflow button)

**Time to complete:** ~3-5 minutes

### `.github/workflows/stress-test.yml`
**What it does:**
1. Waits for build-push workflow to succeed
2. Starts your Flask backend
3. Runs `/stress-test` endpoint
4. Shows CPU/Memory metrics
5. Tests error injection
6. Logs results for Aegis

**Triggered by:**
- Successful completion of `build-push-ecr.yml`
- Manual trigger

**Time to complete:** ~2 minutes

---

## Troubleshooting

### Problem: "Repository does not exist"
**Cause:** ECR repository not created

**Fix:**
```bash
aws ecr create-repository \
  --repository-name aegis-devops-backend \
  --region us-east-1
```

### Problem: "Access Denied" in GitHub Actions
**Cause:** AWS credentials missing or incorrect

**Fix:**
1. Go to your GitHub repo → Settings → Secrets
2. Verify all 3 secrets exist:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
3. Double-check the values (no extra spaces)
4. Regenerate credentials if needed

### Problem: "Docker build step failing"
**Cause:** Missing dependencies in `requirements.txt`

**Fix:**
1. Test locally: `python app.py`
2. If import errors appear, add to `requirements.txt`
3. Commit and push again
4. GitHub Actions will retry

### Problem: "Tests failing in Actions"
**Cause:** Backend not starting or tests timing out

**Fix:**
```bash
# In .github/workflows/stress-test.yml:
sleep 3  # Increase this to 5 if needed
```

---

## What Happens Next (After GitHub Actions)

Once GitHub Actions successfully pushes to ECR:

### 1. AWS Agent (Handled by AWS team)
- Detects new image in ECR
- Updates ECS task definition
- Pulls new image and deploys
- Restarts ECS service

### 2. Orchestrator Agent
- Monitors your backend
- Watches for errors in CloudWatch logs
- Routes to appropriate agent

### 3. GitHub Agent
- If code change needed:
  - Pulls repo
  - Makes fix
  - Pushes back to GitHub
  - Triggers GitHub Actions (your workflow)
  - Redeploys via AWS

---

## Monitoring Workflow Status

### In GitHub
1. **Actions** tab shows all runs
2. Green ✓ = Success
3. Red ✗ = Failed
4. Orange ⟳ = Running

### In AWS
```bash
# View images in ECR
aws ecr describe-images \
  --repository-name aegis-devops-backend \
  --region us-east-1 \
  --query 'imageDetails[*].[imageTags,imagePushedAt]'

# View image layers
aws ecr describe-image-layers \
  --repository-name aegis-devops-backend \
  --region us-east-1
```

---

## Typical Development Workflow

```bash
# 1. Make changes to app.py
nano app.py

# 2. Test locally
python app.py  # ✓ Works

# 3. Commit and push
git add app.py
git commit -m "Fix memory leak detection"
git push origin main

# 4. GitHub Actions automatically:
#    - Builds Docker image
#    - Runs tests
#    - Pushes to ECR
#    Watch in: GitHub repo → Actions

# 5. AWS Agent automatically:
#    - Detects new image
#    - Updates ECS
#    - Deploys new version

# 6. Orchestrator automatically:
#    - Monitors new deployment
#    - Routes errors appropriately
```

---

## CI/CD Pipeline Summary

```
Your Code Commit
      ↓
GitHub Actions Triggered
      ├─ Build Docker Image (2 min)
      ├─ Run Tests (1 min)
      └─ Push to AWS ECR (1 min)
           ↓
ECR Repository Updated
      ↓
AWS Agent Notified
      ├─ Update ECS Task Def
      ├─ Pull New Image
      └─ Redeploy Service (2 min)
           ↓
Service Running with New Code
      ↓
Aegis Orchestrator Monitors
      ├─ Health checks
      ├─ Error detection
      └─ Agent routing
```

---

## For the Demo

**Show the judges:**

1. **Start with push**:
   ```bash
   git push origin main
   ```

2. **Show GitHub Actions running**:
   - Repo → Actions
   - Click running workflow
   - Show each step completing

3. **Show ECR image**:
   ```bash
   aws ecr describe-images --repository-name aegis-devops-backend
   ```

4. **Show it deployed** (AWS team will show this):
   - ECR → Your image with green checkmark
   - ECS service running new image

5. **Show the full cycle**:
   - Make a code change
   - Push to GitHub
   - Watch CI/CD pipeline
   - See new image deployed

**Judge's reaction**: "Wow, they've got a real DevOps pipeline! 🚀"

---

## Quick Reference Commands

```bash
# Test locally first
python app.py

# Push changes (triggers CI/CD)
git push origin main

# Check GitHub Actions
gh actions view  # If GitHub CLI installed

# Check ECR images
aws ecr describe-images --repository-name aegis-devops-backend

# Manual trigger in GitHub Actions
gh workflow run build-push-ecr.yml

# View workflow logs
gh workflow view build-push-ecr.yml --log
```

---

## Checklist Before Demo

- [ ] GitHub secrets configured (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
- [ ] ECR repository created
- [ ] First workflow run successful
- [ ] Image visible in AWS ECR
- [ ] Code can be modified and re-pushed
- [ ] Stress test workflow runs after ECR push
- [ ] All metrics visible in status endpoint

---

**You're ready! 🚀 Push your code and watch the magic happen!**
