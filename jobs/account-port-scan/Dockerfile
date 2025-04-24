# FROM python:3.12-slim

# WORKDIR /usr/src/app

# # Install uv
# RUN pip install --upgrade pip && \
#     pip install uv

# # Copy requirements file
# COPY requirements.txt ./

# # Create virtual environment and install dependencies with uv in one step
# RUN uv venv /usr/src/app/venv && \
#     uv pip install --python=/usr/src/app/venv/bin/python --no-cache -r requirements.txt

# # Copy application files
# COPY port-scan-report.py ./app.py
# COPY logging.json ./logging.json

# # Make the script executable
# RUN chmod +x app.py

# # Set PATH to use the Python from the virtual environment
# ENV PATH="/usr/src/app/venv/bin:$PATH"

# # Default command
# ENTRYPOINT ["./app.py"]

FROM python:3.12-slim

WORKDIR /usr/src/app

# Install uv
RUN pip install --upgrade pip && \
    pip install uv

# Copy requirements file
COPY requirements.txt ./

# Create virtual environment and install dependencies with uv
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install --no-cache -r requirements.txt

# Copy application files
COPY port-scan-report.py ./app.py
COPY logging.json ./logging.json

# Make the script executable
RUN chmod +x app.py

# Set PATH to use the Python from the virtual environment
ENV PATH="/usr/src/app/.venv/bin:$PATH"

# Default command
ENTRYPOINT ["./app.py"]