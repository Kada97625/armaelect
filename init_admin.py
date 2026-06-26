import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, init_db
from app.models import Tenant, User
from app.services.security_service import hash_password
from app.config import get_settings

settings = get_settings()

print("=== ARMAELECT - Initialisation Système ===")

# 1. Init DB
init_db()
db = SessionLocal()

# 2. Création du Tenant Maître (Revendeur)
master_tenant = db.query(Tenant).filter(Tenant.slug == "master").first()
if not master_tenant:
    master_tenant = Tenant(
        name="ARMAELECT Master",
        slug="master",
        contact_email="admin@armaelect.local",
        monthly_document_quota=0 # Illimité
    )
    db.add(master_tenant)
    db.commit()
    db.refresh(master_tenant)
    print(f"✅ Tenant Maître créé (ID: {master_tenant.id})")
else:
    print(f"ℹ️ Tenant Maître existe déjà (ID: {master_tenant.id})")

# 3. Création de l'Utilisateur Super Admin
admin_user = db.query(User).filter(User.email == "admin").first()
if not admin_user:
    # Hachage sécurisé du mot de passe admin
    # Par défaut, le mot de passe est celui configuré dans .env (ou 'adminpass123' par défaut)
    # Note: En prod, changez ce mot de passe!
    admin_user = User(
        tenant_id=master_tenant.id,
        email="admin",
        hashed_password=settings.admin_password_hash,
        full_name="Super Administrateur",
        role="admin",
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    print("✅ Utilisateur Super Admin créé (login: 'admin')")
else:
    print("ℹ️ Utilisateur Super Admin existe déjà")

# 4. Création d'un client de démo (optionnel)
demo_tenant = db.query(Tenant).filter(Tenant.slug == "demo").first()
if not demo_tenant:
    demo_tenant = Tenant(name="Entreprise Démo", slug="demo", contact_email="demo@client.local", monthly_document_quota=50)
    db.add(demo_tenant)
    db.commit()
    db.refresh(demo_tenant)
    demo_user = User(tenant_id=demo_tenant.id, email="demo@client.local", hashed_password=hash_password("demo123"), full_name="Utilisateur Démo", role="member")
    db.add(demo_user)
    db.commit()
    print("✅ Client Démo créé (login: demo@client.local / demo123)")
else:
    print("ℹ️ Client Démo existe déjà")

db.close()
print("=== Initialisation Terminée ===")
print("Lancez l'application avec: uvicorn app.main:app --reload --port 8000")
