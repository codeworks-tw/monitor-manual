FROM python:3.9-slim

# Install wkhtmltopdf and fonts for supporting chinese characters in pdf files
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    fonts-wqy-microhei \
    ttf-wqy-microhei \
    fonts-wqy-zenhei \
    ttf-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run the application
CMD exec functions-framework --target=main --port=${PORT} --debug 