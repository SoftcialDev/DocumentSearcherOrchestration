# Single image for backend (Python) + frontend (Node 20) running together

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8

# ---------- Base system deps ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gnupg2 apt-transport-https \
    iproute2 \
    unixodbc unixodbc-dev \
    openjdk-21-jre-headless \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# ---------- Node.js 20 (for frontend dev server) ----------
# Use NodeSource repo on Debian
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get update && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

# ---------- Selenium / Chromium ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver \
    fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 libdrm2 libgbm1 \
    libgtk-3-0 libnspr4 libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxcursor1 libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 \
    libxkbcommon0 \
 && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER=/usr/bin/chromedriver \
    JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# ---------- Python deps ----------
WORKDIR /app
COPY document-searcher-backend/requirements.txt /app/requirements.txt

RUN pip install --upgrade pip \
 && pip install --no-cache-dir torch==2.2.2+cpu torchvision==0.17.2+cpu torchaudio==2.2.2+cpu \
      -f https://download.pytorch.org/whl/cpu/torch_stable.html \
 && pip install --no-cache-dir -r /app/requirements.txt

RUN apt-get purge -y build-essential && apt-get autoremove -y

# ---------- Copy backend ----------
COPY document-searcher-backend/src/. /app/

# ---------- Frontend deps + code ----------
WORKDIR /frontend
COPY document-searcher-frontend/package*.json /frontend/
RUN npm ci
COPY document-searcher-frontend/ /frontend/

# Helpful for dev servers in containers
ENV HOST=0.0.0.0 \
    CHOKIDAR_USEPOLLING=true \
    NODE_ENV=development

# ---------- Entry point to run both processes ----------
WORKDIR /
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose both ports (backend 5000, CRA 3000)
EXPOSE 5000 3000

# CMD launches both services
CMD ["/entrypoint.sh"]
