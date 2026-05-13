import sys
import cv2
import pickle
import face_recognition
import pyodbc

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout,
    QPushButton, QLineEdit, QFormLayout, QFrame
)
from PySide6.QtGui import QPixmap, QFont, QImage
from PySide6.QtCore import Qt, QTimer

# ===============================
# CONFIGURACIÓN
# ===============================
VIDEO_URL = "http://192.168.0.3:8080/video"

# ===============================
# BASE DE DATOS
# ===============================
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=KioscoHospital;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# =====================================================
class KioskUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GestoFacer")
        self.showFullScreen()

        self.frame_actual = None
        self.contador_rostro = 0
        self.reconocido = False

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.logo = QLabel()
        self.logo.setPixmap(
            QPixmap("assets/logo_principal.png").scaled(150,150,Qt.KeepAspectRatio)
        )
        self.logo.setAlignment(Qt.AlignCenter)

        self.estado = QLabel("Mire a la cámara")
        self.estado.setFont(QFont("Arial", 20, QFont.Bold))
        self.estado.setAlignment(Qt.AlignCenter)

