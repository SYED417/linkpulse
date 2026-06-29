# Start from an official, slim Python image (small but complete).
FROM python:3.11-slim

# All following commands run inside this folder in the container.
WORKDIR /app

# Copy ONLY requirements first. This lets Docker cache the pip install
# layer, so changing app code later doesn't reinstall everything.
COPY requirements.txt .

# Install Python dependencies. --no-cache-dir keeps the image smaller.
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application code into /app.
COPY . .

# Document that the app listens on port 8000.
EXPOSE 8000

# Start the server. host 0.0.0.0 = listen on all interfaces inside the
# container (required so it's reachable from outside the container).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
