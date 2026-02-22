# Switching to 'bookworm' which often has more recent security patches than general 'slim'

FROM python:3.12-slim-bookworm

WORKDIR /app

# Install system dependencies + Redis + Security Updates
RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get install -y \
    build-essential \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip freeze | grep -i jose || true
RUN pip uninstall -y jose python-jose || true
RUN pip install --no-cache-dir python-jose[cryptography]==3.5.0
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copy and setup start script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]