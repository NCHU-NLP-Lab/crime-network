FROM python:3.8-slim
LABEL maintainer="Tomy Hsieh @tomy0000000"

WORKDIR /usr/src/crime-network

# Copy Application
COPY . .

# Upgrade pip & install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

ENTRYPOINT python manage.py runserver 0.0.0.0:8000
