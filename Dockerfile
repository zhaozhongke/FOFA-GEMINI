# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
# This is done in a separate step to leverage Docker's layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's source code into the container
COPY . .

# Expose the port that Gunicorn will run on
EXPOSE 8080

# Define the command to run the application using Gunicorn.
# We run Gunicorn with 4 worker processes. This number can be tuned based on the server's resources.
# We bind to 0.0.0.0 to make the server accessible from outside the container.
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8080", "wsgi:app"]
