FROM python:3.8.0

RUN mkdir -p /app/reports/
WORKDIR /app/
COPY . /app/
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "epiphany.py"]