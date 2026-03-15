# Multi-stage Dockerfile for AegisDevOps Backend
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies (including Gunicorn for production)
COPY requirements.txt .
# Ensure gunicorn is in your requirements.txt or install it explicitly here
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code
COPY app.py .
COPY requirements.txt .

# Health check
# Added 'pip install requests' check or curl, as python-slim doesn't have requests installed by default
# Using wget is more reliable in slim containers
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:5000/health || exit 1

# Expose port
EXPOSE 5000

# Run the app with Gunicorn
# -w 4: Spawns 4 worker processes (adjust based on CPU cores)
# -b 0.0.0.0:5000: Binds to all interfaces on port 5000
# app:app: Tells gunicorn to look for the 'app' object inside 'app.py'
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
