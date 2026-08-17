FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and static assets
COPY . .

# data/ and uploads/ are backed by PersistentVolumes in Kubernetes.
# Create them so the app also works when run as a plain container.
RUN mkdir -p /app/data /app/uploads

# Run as a non-root user (least privilege). fsGroup in the Pod spec makes
# the mounted volumes group-writable for this uid/gid.
RUN useradd --uid 10001 --create-home appuser \
    && chown -R 10001:10001 /app
USER 10001

EXPOSE 5000

# A single gunicorn worker keeps the JSON files safe from concurrent writes.
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "--timeout", "60", "server:app"]
