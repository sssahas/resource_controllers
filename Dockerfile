FROM node:22-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    software-properties-common \
    gcc \
    make \
    unzip \
    libffi-dev \
    libssl-dev \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

RUN npm install -g aws-cdk

WORKDIR /app/cdk

COPY requirements.txt .
RUN pip3.11 install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python3.11", "app.py"]
