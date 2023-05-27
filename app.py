import time
from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST, Histogram, Gauge

load_dotenv()
DB_NAME = os.getenv('DB_NAME')
APP_HOST = os.getenv('APP_HOST')
APP_PORT = os.getenv('APP_PORT')
IS_DEBUG = os.getenv('IS_DEBUG')

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.debug = True
users_seen = {}

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, DB_NAME)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
metrics = PrometheusMetrics(app)

REQUEST_COUNT = Counter('ALABAMA_REQUEST', 'Number of requests served')
# Создаем метрику REQUEST_LATENCY
request_latency_metric = Histogram('REQUEST_LATENCY', 'Request latency')
# Define Prometheus metrics
DB_QUERY_COUNT = Counter('db_query_count', 'Number of database queries')
DB_QUERY_LATENCY = Histogram('db_query_latency_seconds', 'Latency of database queries')

class Appointment(db.Model):
    __tablename__ = 'doctorTime'

    id = db.Column(db.Integer, primary_key=True)
    doctor = db.Column(db.String(50), nullable=False)
    patient = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(50), nullable=False)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@app.route('/show', methods=['GET'])
def get_appointments():
    REQUEST_COUNT.inc()
    with request_latency_metric.time():
        appointments = Appointment.query.all()
        time.sleep(5)
        return [appointment.as_dict() for appointment in appointments]


@app.route("/delete/<patient>", methods=['DELETE'])
def delete_appointment(patient):
    Appointment.query.filter_by(patient=patient).delete()
    db.session.commit()
    return jsonify(success=True)


@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route('/record', methods=['POST'])
def create_appointment():
    # Start timer for query latency
    start_time = time.time()

    doctor = request.json.get('doctor')
    patient = request.json.get('patient')
    date = request.json.get('date') 
    # Check if there is already an appointment at the same time
    existing_appointment = Appointment.query.filter_by(doctor=doctor, date=date).first()
    if existing_appointment:
        return jsonify(success=False, message='This time slot is already taken')
    new_appointment = Appointment(doctor=doctor, patient=patient, date=date)
    db.session.add(new_appointment)
    db.session.commit()

    # Increase query count
    DB_QUERY_COUNT.inc()
    # Record query latency
    DB_QUERY_LATENCY.observe(time.time() - start_time)

    return jsonify(success=True, appointment=new_appointment.as_dict())


if __name__ == '__main__':
    app.run(host=APP_HOST, port=APP_PORT, debug=IS_DEBUG)