import os, uuid, time, re
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator, constr
from typing import Annotated

app = FastAPI(title="Reclutamiento Local API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorio de subidas robusto:
# - Usa variable de entorno UPLOAD_DIR si existe; si no, crea ./uploads junto a main.py
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
CV_DIR = UPLOAD_DIR / "cv"

VIDEO_DIR = UPLOAD_DIR / "video"
PREGUNTAS_DIR = UPLOAD_DIR / "preguntas"

@app.on_event("startup")
def ensure_upload_dirs():
    CV_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    PREGUNTAS_DIR.mkdir(parents=True, exist_ok=True)
RUT_CLEAN_RE = re.compile(r"[^0-9kK]")

def clean_rut(rut: str) -> str:
    return RUT_CLEAN_RE.sub("", rut or "").upper()

def validate_rut(rut: str) -> bool:
    """Valida RUT chileno usando la regla 2,3,4,5,6,7... (de derecha a izquierda).
    - Se calcula suma(d_i * m_i) con multiplicadores cíclicos 2..7
    - dv = 11 - (suma % 11); 10 -> 'K', 11 -> '0'
    """
    r = clean_rut(rut)
    if len(r) < 2:
        return False
    body, dv = r[:-1], r[-1]
    if not body.isdigit():
        return False
    seq = [2,3,4,5,6,7]
    s = 0
    mul_idx = 0
    for ch in reversed(body):
        s += int(ch) * seq[mul_idx]
        mul_idx = (mul_idx + 1) % len(seq)
    res = 11 - (s % 11)
    dv_calc = "0" if res == 11 else "K" if res == 10 else str(res)
    return dv_calc == dv


class ApplicationIn(BaseModel):
    rut: Annotated[str, constr(strip_whitespace=True)]
    full_name: Annotated[str, constr(min_length=3, max_length=120)]

    @field_validator("rut")
    @classmethod
    def _check_rut(cls, v: str) -> str:
        if not validate_rut(v):
            raise ValueError("RUT inválido")
        return v

class AnswersIn(BaseModel):
    application_id: str
    q1: str
    q2: str
    q3: str

# Demo "DB"
DB = {"apps": {}, "answers": {}, "files": {}}

@app.post("/applications")
def create_application(data: ApplicationIn):
    app_id = uuid.uuid4().hex
    DB["apps"][app_id] = {"rut": clean_rut(data.rut), "full_name": data.full_name, "created_at": int(time.time())}
    return {"application_id": app_id}

@app.post("/answers")
def save_answers(data: AnswersIn):
    if data.application_id not in DB["apps"]:
        return {"ok": False, "error": "application_not_found"}
    ans_obj = {"q1": data.q1, "q2": data.q2, "q3": data.q3, "saved_at": int(time.time())}
    DB["answers"][data.application_id] = ans_obj
    # Guardar en preguntas/<nombre>_<rut>.json
    import json
    app_data = DB["apps"].get(data.application_id, {})
    nombre = app_data.get("full_name", "sin_nombre").replace(" ", "_")
    rut = app_data.get("rut", "sin_rut")
    preguntas_path = PREGUNTAS_DIR / f"{nombre}_{rut}.json"
    with open(preguntas_path, "w", encoding="utf-8") as f:
        json.dump(ans_obj, f, ensure_ascii=False, indent=2)
    return {"ok": True, "file": str(preguntas_path)}

def _safe_name(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".", " ")).strip()

@app.post("/upload/cv")
async def upload_cv(application_id: str = Form(...), file: UploadFile = File(...)):
    if application_id not in DB["apps"]:
        return {"ok": False, "error": "application_not_found"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".pdf", ".doc", ".docx"):
        return {"ok": False, "error": "invalid_extension"}
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10 MB
        return {"ok": False, "error": "file_too_large"}
    fname = f"{int(time.time())}-{application_id}-{_safe_name(file.filename)}"
    path = CV_DIR / fname
    with open(path, "wb") as f:
        f.write(contents)
    DB["files"].setdefault(application_id, {})["cv"] = str(path)
    return {"ok": True, "stored_path": str(path)}

@app.post("/upload/video")
async def upload_video(application_id: str = Form(...), file: UploadFile = File(...)): 
    if application_id not in DB["apps"]: 
        return {"ok": False, "error": "application_not_found"} 
    ext = os.path.splitext(file.filename or "")[1].lower() 
    if ext not in (".webm", ".mp4"): 
        return {"ok": False, "error": "invalid_extension"} 
    contents = await file.read() 
    if len(contents) > 200 * 1024 * 1024: # 200 MB
         return {"ok": False, "error": "file_too_large"} 
    fname = f"{int(time.time())}-{application_id}-{_safe_name(file.filename)}"
    path = VIDEO_DIR / fname 
    with open(path, "wb") as f: 
        f.write(contents) 
        DB["files"].setdefault(application_id, {})["video"] = str(path) 
        return {"ok": True, "stored_path": str(path)} 
    # ...existing code...
# Endpoint de depuración de rutas
@app.get("/_debug/paths")
def debug_paths():
    return {
        "base_dir": str(BASE_DIR),
        "upload_dir": str(UPLOAD_DIR),
        "cv_dir": str(CV_DIR),
        "video_dir": str(VIDEO_DIR),
        "exists": {
            "upload": UPLOAD_DIR.exists(),
            "cv": CV_DIR.exists(),
            "video": VIDEO_DIR.exists()
        }
    }

@app.get("/health")
def health():
    return {"ok": True}
@app.get("/application/{application_id}")
def get_application(application_id: str):
    if application_id not in DB["apps"]:
        raise HTTPException(status_code=404, detail="application not found")

    app_data = DB["apps"][application_id]
    answers = DB["answers"].get(application_id, {})
    files = DB["files"].get(application_id, {})

    result = {
        "application_id": application_id,
        "rut": app_data["rut"],
        "full_name": app_data["full_name"],
        "created_at": app_data["created_at"],
        "answers": answers,
        "files": files
    }

    # Guardar JSON físico en uploads/
    json_path = os.path.join(UPLOAD_DIR, f"{application_id}.json")
    import json
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
