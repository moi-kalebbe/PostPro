# Use official Python runtime as a parent image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libffi-dev \
    pkg-config \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Prefer IPv4 over IPv6
RUN echo "precedence ::ffff:0:0/96  100" >> /etc/gai.conf

# Install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --prefer-binary -r requirements.txt

# Copy project
COPY . /app/

# Create entrypoint script
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Run entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
