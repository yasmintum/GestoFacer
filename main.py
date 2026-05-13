
from fastapi import FastAPI, UploadFile, File
import shutil, pickle
from database import cursor
from register_patient import obtener_encoding, comparar

app = FastAPI()

@app.post("/reconocer")
async def reconocer(file: UploadFile = File(...)):
    ruta = f"fotos/{file.filename}"
    with open(ruta, "wb") as f:
        shutil.copyfileobj(file.file, f)

    encoding = obtener_encoding(ruta)
    if encoding is None:
        return {"error": "No se detectó rostro"}

    cursor.execute("SELECT id, face_encoding FROM pacientes")
    data = cursor.fetchall()

    ids, encodings = [], []
    for pid, face in data:
        ids.append(pid)
        encodings.append(pickle.loads(face))

    match = comparar(encodings, encoding)

    if match is not None:
        paciente_id = ids[match]
        cursor.execute(
            "SELECT fecha, hora, doctor FROM citas WHERE paciente_id=?",
            (paciente_id,)
        )
        cita = cursor.fetchone()

        if cita:
            return {
                "encontrado": True,
                "cita": {
                    "fecha": cita[0],
                    "hora": cita[1],
                    "doctor": cita[2]
                }
            }
        else:
            return {"encontrado": True, "cita": None}

    return {"encontrado": False}