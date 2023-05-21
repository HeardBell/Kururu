FROM python:3.9-alpine

WORKDIR /Kurilenko_Lab2

COPY . .


RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]