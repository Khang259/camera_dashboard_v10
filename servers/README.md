#Code base structure

servers/
├── ai-training/
│   └── yolov8/
│       ├── active_learning.py
│       ├── annotation_guide.md
│       ├── auto_labeling.py
│       ├── automation.py
│       ├── dataset_setup.py
│       ├── detect.py
│       ├── README.md
│       ├── requirements.txt
│       ├── train.py
│       └── datasets/
│           ├── datasets/
│           │   └── items/
│           │       ├── classes.txt
│           │       └── data.yaml
│           ├── pre-train/
│           │   ├── data/
│           │   │   └── (nhiều file ảnh .jpg)
│           │   └── data_collector.py
│           └── unlabeled/
│               └── (nhiều file ảnh .jpg)
├── main/
│   ├── logs/
│   │   ├── requests_20250513.log
│   │   └── requests_20250514.log
│   └── main.py
├── signaling-server/
│   ├── logs/
│   │   ├── requests_20250514.log
│   │   └── requests_signaling_20250514.log
│   └── signaling_server.py
├── webrtc-server/
│   ├── __pycache__/
│   │   ├── config.cpython-310.pyc
│   │   ├── config.cpython-311.pyc
│   │   ├── detector.cpython-311.pyc
│   │   ├── object_detection.cpython-310.pyc
│   │   └── object_detection.cpython-311.pyc
│   ├── config.py
│   ├── detector.py
│   ├── logs/
│   │   ├── requests_20250514.log
│   │   └── requests_webrtc_server_20250514.log
│   ├── object_detection.py
│   ├── webrtc_server.log
│   └── webrtc_server.py
├── __pycache__/
├── config.json
└── requirements.txt