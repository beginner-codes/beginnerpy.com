FROM python:3.8-slim-buster
MAINTAINER Zech Zimmerman "hi@zech.codes"

WORKDIR /usr/src/app
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install

USER 1000:1000

COPY static .
COPY templates .
COPY models.py .
COPY app.py .
CMD ["poetry", "run", "gunicorn", "-w 4", "--bind=0.0.0.0:5000", "app:app"]
