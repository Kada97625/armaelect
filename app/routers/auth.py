from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.services.security_service import hash_password, verify_password
from app.services.auth_service import create_access_token, verify_master_admin
from app.crud import create_user, get_user_by_email, create_tenant, get_tenant_by_slug

router = APIRouter(prefix="/auth", tags=["Authentification"])

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    tenant_name: str
    slug: str
    admin_email: str
    admin_password: str

class MasterRegisterRequest(BaseModel):
    tenant_name: str
    slug: str
    admin_email: str
    admin_password: str
    master_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    tenant_name: str
    role: str

@router.post("/login", response_model=Token)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    tenant = user.tenant
    access_token = create_access_token(data={"sub": user.email, "tenant_id": tenant.id, "role": user.role})
    return Token(access_token=access_token, token_type="bearer", tenant_name=tenant.name, role=user.role)

# --- Inscription Libre (pour le mode SaaS public) ---
# Tu peux désactiver cette route si tu veux que le revendeur crée les clients manuellement
@router.post("/register", response_model=Token)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if get_tenant_by_slug(db, data.slug):
        raise HTTPException(status_code=400, detail="Ce slug est déjà utilisé")
    if get_user_by_email(db, data.admin_email):
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    
    tenant = create_tenant(db, name=data.tenant_name, slug=data.slug, contact_email=data.admin_email)
    hashed_pw = hash_password(data.admin_password)
    user = create_user(db, tenant_id=tenant.id, email=data.admin_email, hashed_password=hashed_pw, full_name="Administrateur", role="admin")
    
    access_token = create_access_token(data={"sub": user.email, "tenant_id": tenant.id, "role": "admin"})
    return Token(access_token=access_token, token_type="bearer", tenant_name=tenant.name, role="admin")

# --- Création par le Revendeur Maître ---
@router.post("/master/create-tenant", response_model=Token)
def master_create_tenant(data: MasterRegisterRequest, db: Session = Depends(get_db)):
    verify_master_admin(data.master_password)
    return register(RegisterRequest(**data.model_dump(exclude={'master_password'})), db)