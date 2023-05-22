import time
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter

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

REQUEST_COUNT = Counter('request_count', 'Number of requests served')

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
    appointments = Appointment.query.all()
    time.sleep(15)
    return [appointment.as_dict() for appointment in appointments]


@app.route("/delete/<patient>", methods=['DELETE'])
def delete_appointment(patient):
    Appointment.query.filter_by(patient=patient).delete()
    db.session.commit()
    return jsonify(success=True)


@app.route('/record', methods=['POST'])
def create_appointment():
    REQUEST_COUNT.ink()
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
    return jsonify(success=True, appointment=new_appointment.as_dict())

if __name__ == '__main__':
    app.run(host=APP_HOST, port=APP_PORT, debug=IS_DEBUG)