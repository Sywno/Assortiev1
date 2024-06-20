FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . /app/
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY envi.env /app/envi.env
RUN export $(cat /app/envi.env | xargs)

RUN python manage.py collectstatic --noinput
RUN python manage.py migrate

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
