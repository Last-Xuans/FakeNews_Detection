FROM python:3.8-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 7860

RUN chmod +x ./run.sh

CMD ["./run.sh"]
