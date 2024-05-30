FROM python:3.12-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY port-scan-report.py ./app.py
COPY logging.json ./logging.json

# Copy the entrypoint script and make it executable
RUN chmod +x app.py

# Default command
ENTRYPOINT [ "./app.py" ]
