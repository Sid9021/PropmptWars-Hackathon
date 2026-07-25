FROM python:3.11-slim

# Install Nginx
RUN apt-get update && \
    apt-get install -y nginx && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Copy Nginx config to system directory
RUN cp nginx.conf /etc/nginx/nginx.conf

# Make the start script executable
RUN chmod +x start.sh

# Expose a default port (Render will override this)
EXPOSE 8080

# Run the startup script
CMD ["./start.sh"]
