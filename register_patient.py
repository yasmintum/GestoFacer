import sys
import cv2
import pickle
import face_recognition
import pyodbc

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QLineEdit, QVBoxLayout, QHBoxLayout, QFormLayout, QFrame
)
from PySide6.QtGui import QPixmap, QFont, QImage
from PySide6.QtCore import Qt, QTimer

VIDEO_URL = "http://192.168.0.6:8080/video"
TOLERANCE = 0.32
MAX_DISTANCE = 0.36

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


class KioskUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GestoFacer")
        self.showFullScreen()

        self.frame = None
        self.encoding = None
        self.frozen = False

        # ===== LAYOUT PRINCIPAL =====
        main = QVBoxLayout(self)
        main.setSpacing(10)

        # ===== LOGO GRANDE =====
        self.logo = QLabel()
        self.logo.setPixmap(
            QPixmap("assets/logo_principal.png").scaledToHeight(140)
        )
        self.logo.setAlignment(Qt.AlignCenter)
        main.addWidget(self.logo)

        # ===== STATUS =====
        self.status = QLabel("Colóquese frente a la cámara")
        self.status.setFont(QFont("Arial", 22, QFont.Bold))
        self.status.setAlignment(Qt.AlignCenter)
        main.addWidget(self.status)

        # ===== CONTENIDO =====
        content = QHBoxLayout()

        # ===== CAMARA =====
        self.camera = QLabel()
        self.camera.setFixedSize(720, 520)
        self.camera.setStyleSheet("""
            border:3px solid #1E90FF;
            border-radius:15px;
            background-color: white;
        """)
        content.addWidget(self.camera)

        # ===== PANEL DERECHO =====
        self.panel = QFrame()
        self.panel.setFixedWidth(380)
        self.panel.setStyleSheet("""
            background-color: white;
            border-radius: 15px;
            padding: 15px;
        """)
        self.panel_layout = QVBoxLayout(self.panel)

        content.addWidget(self.panel)

        main.addLayout(content)

        # ===== BOTONES GRANDES =====
        self.btn_capture = QPushButton("📸 Tomar foto")
        self.btn_identify = QPushButton("🔍 Identificar")
        self.btn_reset = QPushButton("🔄 Reiniciar")

        self.btn_identify.setEnabled(False)

        self.btn_capture.clicked.connect(self.capture)
        self.btn_identify.clicked.connect(self.identify)
        self.btn_reset.clicked.connect(self.reset)

        for btn in [self.btn_capture, self.btn_identify, self.btn_reset]:
            btn.setFixedHeight(60)
            btn.setFont(QFont("Arial", 16, QFont.Bold))

        self.btn_capture.setStyleSheet("background:#0078D7;color:white;border-radius:10px;")
        self.btn_identify.setStyleSheet("background:#28A745;color:white;border-radius:10px;")
        self.btn_reset.setStyleSheet("background:#6C757D;color:white;border-radius:10px;")

        self.panel_layout.addWidget(self.btn_capture)
        self.panel_layout.addWidget(self.btn_identify)
        self.panel_layout.addWidget(self.btn_reset)

        # ===== CAMARA =====
        self.cap = cv2.VideoCapture(VIDEO_URL)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(40)

        # Fondo blanco general
        self.setStyleSheet("background-color: white;")

    # ===============================
    def update(self):
        if self.frozen:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.resize(frame, (720, 520))
        self.frame = frame.copy()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        display = frame.copy()

        if len(faces) == 1:
            x, y, w, h = faces[0]
            cv2.rectangle(display, (x, y), (x+w, y+h), (0, 255, 0), 2)
        else:
            self.encoding = None
            self.btn_identify.setEnabled(False)

        rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        self.camera.setPixmap(QPixmap.fromImage(QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)))

    # ===============================
    def capture(self):
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        if len(faces) != 1:
            self.status.setText("❌ Debe haber un solo rostro")
            return

        enc = face_recognition.face_encodings(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB))
        if not enc:
            return

        self.encoding = enc[0]
        self.frozen = True
        self.btn_identify.setEnabled(True)

        self.status.setText("✅ Foto capturada")

    # ===============================
    def identify(self):
        cursor.execute("SELECT * FROM Pacientes")

        for row in cursor.fetchall():
            known = pickle.loads(row.FaceEncoding)
            dist = face_recognition.face_distance([known], self.encoding)[0]

            if dist < MAX_DISTANCE:
                self.show_info(row)
                return

        self.show_form()

    # ===============================
    def show_info(self, p):
        self.clear_panel()
        self.status.setText("✅ Paciente reconocido")

        info = QLabel(f"""
<b>Nombre:</b> {p.Nombre} {p.Apellidos}<br>
<b>Teléfono:</b> {p.Telefono}<br>
<b>Email:</b> {p.Email}<br>
<b>DPI:</b> {p.DPI}
""")

        info.setFont(QFont("Arial", 14))
        info.setStyleSheet("""
            background:#E8F5E9;
            padding:15px;
            border-radius:10px;
        """)

        self.panel_layout.addWidget(info)

    # ===============================
    def show_form(self):
        self.clear_panel()
        self.status.setText("❌ No registrado")

        form = QFormLayout()

        self.nombre = QLineEdit()
        self.apellidos = QLineEdit()
        self.tel = QLineEdit()
        self.email = QLineEdit()
        self.dpi = QLineEdit()

        for w in [self.nombre,self.apellidos,self.tel,self.email,self.dpi]:
            w.setStyleSheet("padding:6px; border:2px solid #ccc; border-radius:5px;")

        save = QPushButton("Guardar Registro")
        save.setStyleSheet("background:#0078D7;color:white;padding:10px;border-radius:8px;")
        save.clicked.connect(self.save)

        form.addRow("Nombre:", self.nombre)
        form.addRow("Apellidos:", self.apellidos)
        form.addRow("Teléfono:", self.tel)
        form.addRow("Email:", self.email)
        form.addRow("DPI:", self.dpi)
        form.addRow(save)

        self.panel_layout.addLayout(form)

    # ===============================
    def save(self):
        cursor.execute("""
        INSERT INTO Pacientes
        (Nombre,Apellidos,Telefono,Email,DPI,FaceEncoding)
        VALUES (?,?,?,?,?,?)
        """, (
            self.nombre.text(),
            self.apellidos.text(),
            self.tel.text(),
            self.email.text(),
            self.dpi.text(),
            pickle.dumps(self.encoding)
        ))
        conn.commit()
        self.status.setText("✅ Guardado correctamente")

    # ===============================
    def reset(self):
        self.frozen = False
        self.encoding = None
        self.btn_identify.setEnabled(False)
        self.clear_panel()
        self.status.setText("Colóquese frente a la cámara")

    def clear_panel(self):
        while self.panel_layout.count() > 3:
            w = self.panel_layout.takeAt(3).widget()
            if w:
                w.deleteLater()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = KioskUI()
    ui.show()
    sys.exit(app.exec())