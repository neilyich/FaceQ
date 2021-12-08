from flask import Flask
from multiprocessing import Queue, Process

from CameraReader import read_stream_from_camera
from DatabaseManager import DatabaseManager
from FaceScanner import scan_faces
from Logger import Logger
from QueueManager import process_faces

app = Flask(__name__)

environment_config_classes = {
    'prod': 'ProdConfig',
    'local_prod': 'LocalProdConfig',

    'debug': 'LocalDebugConfig',
    'local_debug': 'LocalDebugConfig',
}

app.config.from_object('config.config.' + environment_config_classes[app.config['ENV']])

print(f'loaded environment: {app.config["ENV"]}')

logger = Logger(app.config['DEBUG'])

detected_faces = Queue()
frames_queue = Queue(app.config['FRAMES_QUEUE_MAX_SIZE'])

for i in range(app.config['FACE_DETECTION_THREADS_COUNT']):
    face_scanner = Process(target=scan_faces,
                           args=(detected_faces, frames_queue, logger),
                           daemon=True)
    face_scanner.start()

face_processor = Process(target=process_faces,
                         args=(detected_faces,
                               app.config['MIN_FRAMES_WITH_FACE'],
                               app.config['MAX_TEST_FRAMES'],
                               app.config['PRINT_TICKETS'],
                               logger),
                         daemon=True)
face_processor.start()

camera_reader = Process(target=read_stream_from_camera,
                        args=(app.config['CAMERA_LINK'], frames_queue, app.config['FRAMES_QUEUE_MAX_SIZE'], logger),
                        daemon=True)
camera_reader.start()

database_manager = DatabaseManager()