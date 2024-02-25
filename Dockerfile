FROM python:3.11.4-slim

ENV APP_HOME /app

WORKDIR $APP_HOME

COPY . .

EXPOSE 3000

ENTRYPOINT ["python", "main.py"]
