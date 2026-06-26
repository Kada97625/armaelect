from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import init_db
from app.routers import auth, documents, admin
import os

app = FastAPI(title="ARMAELECT SaaS", version="2.0.0", description="Plateforme White-Label de Génération de Documents Techniques")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation DB
init_db()

# Mount Static Files
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Inclusion des Routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(admin.router)

# Route racine pour servir le SPA
@app.get("/")
def serve_spa():
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(path=index_path)
    return {"detail": "Frontend not found"}

# Route de santé
@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}

# Catch-all pour le frontend (si l'utilisateur rafraîchit sur une sous-route)
# Important: doit être APRÈS les routes API pour ne pas les masquer
@app.get("/{full_path:path}")
def spa_catch_all(full_path: str):
    if full_path.startswith("api") or full_path.startswith("auth") or full_path.startswith("health") or full_path.startswith("static"):
        return {"detail": "Route API non trouvée"}
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(path=index_path)
    return {"detail": "Frontend not found"}
