# Reclutamiento Local v2
- Next.js (frontend) + FastAPI (backend) + demo HTML estático.
- Validación de RUT en **cliente y servidor** con regla: multiplicar dígitos de derecha a izquierda por 2,3,4,5,6,7, repetir; sumar; 11 - (suma % 11); 10 -> K, 11 -> 0.

## Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac:
. .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
Abre http://localhost:3000

## HTML demo
```bash
cd html_demo
python -m http.server 8080
```
Abre http://localhost:8080 (requiere el backend arriba en :8000).
