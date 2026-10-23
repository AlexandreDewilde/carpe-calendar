# syntax=docker/dockerfile:1
FROM python:3.14-slim

WORKDIR /code
ENV DJANGO_DEBUG=0

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py makemigrations && python manage.py migrate

# EXPOSE 8000

# CMD ["python", "manage.py", "runserver", "127.0.0.1:8000"]
CMD ["sh", "start.sh"]
