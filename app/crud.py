from sqlalchemy.orm import Session
from app.models import Tenant, User, Document, Template

# ============================================================
# CRUD : Tenant
# ============================================================
def create_tenant(db: Session, name: str, slug: str, contact_email: str = "", config: dict = None):
    tenant = Tenant(name=name, slug=slug, contact_email=contact_email, config_json=str(config).replace("'", '"') if config else "{}")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant

def get_tenant(db: Session, tenant_id: int):
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()

def get_tenant_by_slug(db: Session, slug: str):
    return db.query(Tenant).filter(Tenant.slug == slug).first()

def list_tenants(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Tenant).offset(skip).limit(limit).all()

def update_tenant(db: Session, tenant_id: int, updates: dict):
    tenant = get_tenant(db, tenant_id)
    if not tenant:
        return None
    for key, value in updates.items():
        if hasattr(tenant, key) and key not in ['id', 'created_at']:
            setattr(tenant, key, value)
    db.commit()
    db.refresh(tenant)
    return tenant

# ============================================================
# CRUD : User
# ============================================================
def create_user(db: Session, tenant_id: int, email: str, hashed_password: str, full_name: str = "", role: str = "member"):
    user = User(tenant_id=tenant_id, email=email, hashed_password=hashed_password, full_name=full_name, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def list_users_by_tenant(db: Session, tenant_id: int):
    return db.query(User).filter(User.tenant_id == tenant_id).all()

# ============================================================
# CRUD : Document
# ============================================================
def create_document(db: Session, tenant_id: int, user_id: int, document_type: str, title: str, 
                    project_description: str, client_info: str, extra_context: str = "",
                    raw_markdown: str = "", generated_html: str = "", status: str = "draft"):
    doc = Document(
        tenant_id=tenant_id, user_id=user_id, document_type=document_type, title=title,
        project_description=project_description, client_info=client_info, extra_context=extra_context,
        raw_markdown=raw_markdown, generated_html=generated_html, status=status
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def get_document(db: Session, doc_id: int, tenant_id: int):
    return db.query(Document).filter(Document.id == doc_id, Document.tenant_id == tenant_id).first()

def list_documents(db: Session, tenant_id: int, skip: int = 0, limit: int = 100):
    return db.query(Document).filter(Document.tenant_id == tenant_id).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

# ============================================================
# CRUD : Template
# ============================================================
def create_template(db: Session, tenant_id: int, name: str, template_type: str, system_prompt_override: str = ""):
    tpl = Template(tenant_id=tenant_id, name=name, template_type=template_type, system_prompt_override=system_prompt_override)
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl

def get_templates_by_tenant(db: Session, tenant_id: int, template_type: str = None):
    q = db.query(Template).filter(Template.tenant_id == tenant_id)
    if template_type:
        q = q.filter(Template.template_type == template_type)
    return q.all()