FROM python:3.8.5

RUN apt-get update && apt-get install -y -qq --no-install-recommends netcat
WORKDIR /code
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ["gunicorn", "application.wsgi:application", "--bind", "0.0.0.0:8000"]
