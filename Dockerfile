# Dockerfile

FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
COPY packages.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends $(cat packages.txt) && \
    rm -rf /var/lib/apt/lists/* && \
    rm packages.txt

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs && \
    mkdir -p .streamlit && \
    mkdir -p data/outputs

# Set permissions
RUN chmod -R 755 /app

# Set environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Create non-root user
RUN useradd -m -r appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app.py"]