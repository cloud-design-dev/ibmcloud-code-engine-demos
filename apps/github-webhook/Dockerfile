FROM python:3.12-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY main.py ./main.py
COPY logging.json ./logging.json

# Copy the entrypoint script and make it executable
RUN chmod +x main.py

EXPOSE 5000

# Default command
ENTRYPOINT [ "./main.py" ]
