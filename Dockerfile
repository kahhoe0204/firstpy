# Use the official Python image as the base
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /readPdfApp

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless \
    wget \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Copy the requirements file into the container
COPY requirements.txt requirements.txt

# Install the dependencies
RUN pip3 install -r requirements.txt


# Expose the port on which the app runs
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "readfile:app", "--host", "0.0.0.0", "--port", "8000"]
