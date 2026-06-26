from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import json

# ============================================================
# Modèle : Tenant (Client / Entreprise revendue)
# ============================================================
class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    
    # Identifiants
    slug = Column(String, unique=True, index=True, nullable=False) # ex: " entreprise-dupont"
    name = Column(String, nullable=False)
    logo_url = Column(String, default="")
    primary_color = Column(String, default="#1a365d")
    
    # Contacts
    contact_name = Column(String, default="")
    contact_email = Column(String, default="")
    contact_phone = Column(String, default="")
    
    # Quotas (SaaS)
    monthly_document_quota = Column(Integer, default=100)
    current_month_usage = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Configuration globale du tenant
    config_json = Column(Text, default="{}") # Stockage flexible pour les paramètres spécifiques
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    users = relationship("User", back_populates="tenant")

    @property
    def config(self):
        return json.loads(self.config_json) if self.config_json else {}

# ============================================================
# Modèle : Utilisateur (Membre d'un Tenant)
# ============================================================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, default="")
    role = Column(String, default="member") # 'admin' (tenant) ou 'member'
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="users")

# ============================================================
# Modèle : Document (Devis ou Mémoire Généré)
# ============================================================
class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Métadonnées
    title = Column(String, default="Document sans titre")
    document_type = Column(String, nullable=False) # 'quote' ou 'technical_memo'
    project_description = Column(Text, default="")
    client_info = Column(Text, default="")
    extra_context = Column(Text, default="")
    
    # Contenus
    raw_markdown = Column(Text, default="")
    generated_html = Column(Text, default="")
    pdf_path = Column(String, default="") # Chemin relatif ou lien
    
    # Statut
    status = Column(String, default="draft") # 'draft', 'sent', 'archived'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ============================================================
# Modèle : Template (Modèle personnalisé par Tenant)
# ============================================================
class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    name = Column(String, nullable=False) # ex: "Devis Electrique Standard", "Memoire Hôpital"
    template_type = Column(String, nullable=False) # 'quote' ou 'technical_memo'
    
    # Le prompt système surchargé pour ce template
    system_prompt_override = Column(Text, default="")
    # Ordre des sections spécifique
    section_order_json = Column(Text, default="[]")
    # Configuration de style (couleurs, logo header)
    style_config_json = Column(Text, default="{}")
    
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())