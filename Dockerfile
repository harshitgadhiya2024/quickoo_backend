FROM python:3.9-slim-buster

WORKDIR /app

# Copy your application code
COPY . /app

# Install Flask and other dependencies
RUN pip install --no-cache-dir -r reqdev.txt

EXPOSE 5000

ENV NAME World

# Run the Flask server
CMD ["python", "main.py"]