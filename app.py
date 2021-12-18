from flask import Response, Flask
from flask.helpers import send_from_directory
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS
from src.main import processImage, format_data
import cv2
import threading

frame = None
lock = threading.Lock()
data = None
AR = False

class VideoApiHandler(Resource):
    def get(self):
        return {'resultStatus': "SUCCESS", 'data': data if data else "No code detected", 'url': format_data(data) if data else ""}
    def post(self):
        global AR
        parser = reqparse.RequestParser()
        parser.add_argument('AR', type=str)
        args = parser.parse_args()
        setAR = args['AR']
        if setAR == "True":
            AR = True
        else:
            AR = False
        return {'resultStatus': 'SUCCESS', 'data': data if data else "No code detected", 'url': format_data(data) if data else ""}

app = Flask(__name__, static_url_path='', static_folder='frontend/public')
CORS(app)
api = Api(app)

api.add_resource(VideoApiHandler, '/flask/video_feed')

vc = cv2.VideoCapture(0)

if not vc.isOpened():
        print("Error: Unable to open camera")

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

def detect_codes():
    global frame, lock, data
    while True:
        isRead, frame = vc.read()
        if not isRead:
            break
        processed, codeExists, data = processImage(frame, AR)
        with lock:
            frame = processed.copy()

def encode_frame():
    global frame, lock
    while True:
        with lock:
            if frame is None:
                continue
            flag, encodedFrame = cv2.imencode(".jpg", frame)
            if not flag:
                continue
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedFrame) + b'\r\n')

def start_thread():
    t = threading.Thread(target=detect_codes)
    t.daemon = True
    t.start()

@app.route("/video_feed")
def video_feed():
    start_thread()
    return Response(encode_frame(), mimetype = "multipart/x-mixed-replace; boundary=frame")