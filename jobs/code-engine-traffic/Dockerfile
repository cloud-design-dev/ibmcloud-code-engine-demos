FROM python:3.12-slim

WORKDIR /usr/src/app

COPY requirements.txt ./

# Update package list, install apache2-utils, and clean up in one RUN to keep the image size down
RUN apt-get update && \
    apt-get install -y apache2-utils && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY benchmark.py ./benchmark.py

# Copy the entrypoint script and make it executable
RUN chmod +x benchmark.py

# Default command
ENTRYPOINT [ "./benchmark.py" ]
