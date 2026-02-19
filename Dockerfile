# ==========================================================================================================
# =====================              STAGE 1 - Creation of py wheels                   =====================
# ==========================================================================================================
FROM python:3.12-alpine AS builder

# Install necessary tools 
RUN apk update && apk upgrade --no-interactive
RUN apk add libpq libpq-dev python3-dev build-base linux-headers bash curl lscpu gnupg postgresql-client postgresql-dev --no-interactive

# set work directory
WORKDIR /usr/src/py-req 

# set env variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && pip wheel --no-cache-dir --no-deps --wheel-dir ./wheels -r requirements.txt


# ========================================================================================================================
# =====================              FINAL STAGE - Creation of the app with wheels                   =====================
# ========================================================================================================================
FROM python:3.12-alpine

RUN apk update && apk upgrade --no-interactive
RUN apk add libpq --no-interactive

# set env variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

LABEL Version=$version_number 

WORKDIR /app

COPY --from=builder /usr/src/py-req/wheels/ ./wheels/
COPY --from=builder /usr/src/py-req/requirements.txt .

RUN pip install --upgrade pip \
&& pip install --no-cache ./wheels/*

COPY config ./config
COPY application.py .
COPY core ./core
COPY static ./static
COPY server ./server
RUN mkdir ./logs

# Health check using BusyBox wget (available on Alpine by default).
# Container orchestrators use this to determine application liveness.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5000/health || exit 1