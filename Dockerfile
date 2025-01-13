# Use the official Python image as the base
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a non-root user
RUN useradd --create-home myuser
USER myuser
WORKDIR /home/myuser

# Install system dependencies if needed
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && apt-get clean
USER myuser

# Copy and install Python dependencies
COPY requirements.txt .
RUN python -m venv venv && ./venv/bin/pip install --upgrade pip \
    && ./venv/bin/pip install -r requirements.txt

# Copy the Django project into the container
COPY . .

# Expose the application port (Django default: 8000)
EXPOSE 8000

# Run the Django development server
CMD ["./venv/bin/python", "manage.py", "runserver", "0.0.0.0:8000"]

