from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app.services.auth_service import verify_master_admin
from app.crud import list_tenants, update_tenant, create_tenant, create_user
from app.models import Tenant, Document, User
from app.services.security_service import hash_password

router = APIRouter(prefix="/api/admin", tags=["Administration Revendeur"])

class TenantStats(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool
    usage: int
    quota: int
    contact_email: str
    total_docs: int
    total_users: int

class QuotaUpdate(BaseModel):
    quota: int

@router.get("/stats", response_model=List[TenantStats])
def get_all_stats(master_password: str, db: Session = Depends(get_db)):
    verify_master_admin(master_password)
    
    tenants = list_tenants(db)
    result = []
    for t in tenants:
        doc_count = db.query(Document).filter(Document.tenant_id == t.id).count()
        user_count = db.query(User).filter(User.tenant_id == t.id).count()
        result.append({
            "id": t.id, "name": t.name, "slug": t.slug, "is_active": t.is_active,
            "usage": t.current_month_usage, "quota": t.monthly_document_quota,
            "contact_email": t.contact_email,
            "total_docs": doc_count, "total_users": user_count
        })
    return result

@router.post("/tenants/{tenant_id}/quota")
def update_tenant_quota(tenant_id: int, data: QuotaUpdate, master_password: str, db: Session = Depends(get_db)):
    verify_master_admin(master_password)
    tenant = update_tenant(db, tenant_id, {"monthly_document_quota": data.quota})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    return {"detail": "Quota mis à jour", "new_quota": data.quota}

@router.post("/tenants/{tenant_id}/toggle")
def toggle_tenant(tenant_id: int, master_password: str, db: Session = Depends(get_db)):
    verify_master_admin(master_password)
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    tenant.is_active = not tenant.is_active
    db.commit()
    return {"detail": "Statut mis à jour", "is_active": tenant.is_active}

class TenantCreateReq(BaseModel):
    name: str
    slug: str
    admin_email: str
    admin_password: str
    contact_email: str = ""
    master_password: str

@router.post("/tenants/create")
def admin_create_tenant(data: TenantCreateReq, db: Session = Depends(get_db)):
    verify_master_admin(data.master_password)
    if db.query(Tenant).filter(Tenant.slug == data.slug).first():
        raise HTTPException(status_code=400, detail="Slug déjà utilisé")
    
    tenant = create_tenant(db, name=data.name, slug=data.slug, contact_email=data.contact_email or data.admin_email)
    hashed_pw = hash_password(data.admin_password)
    create_user(db, tenant_id=tenant.id, email=data.admin_email, hashed_password=hashed_pw, full_name="Administrateur", role="admin")
    return {"detail": "Client créé avec succès", "tenant_id": tenant.id, "slug": tenant.slug}
