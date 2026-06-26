from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
from datetime import datetime
from app.database import get_db
from app.services.auth_service import verify_token
from app.services.llm_service import llm_service
from app.services.document_service import doc_service
from app.crud import create_document, list_documents, get_document
from app.models import User

router = APIRouter(prefix="/api/documents", tags=["Documents"])

def generate_pdf_lite(html_content: str, filename: str) -> str:
    """Fallback PDF generation. Retourne un fichier HTML nommé .pdf pour la simplicité."""
    os.makedirs("generated_pdfs", exist_ok=True)
    path = f"generated_pdfs/{filename.replace('.pdf','.html')}"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return path

# ============================================================
# ROUTES API
# ============================================================

class GenerateRequest(BaseModel):
    document_type: str # 'quote' ou 'technical_memo'
    title: str
    project_description: str
    client_info: str
    extra_context: Optional[str] = ""
    template_id: Optional[int] = None

class DocumentOut(BaseModel):
    id: int
    title: str
    document_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/generate", response_model=DocumentOut)
def generate_document(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    tenant = current_user.tenant
    
    # 1. Vérification des quotas
    if tenant.monthly_document_quota > 0 and tenant.current_month_usage >= tenant.monthly_document_quota:
        raise HTTPException(status_code=403, detail="Quota mensuel de documents atteint. Veuillez contacter votre revendeur.")

    # 2. Génération IA
    if request.document_type == 'quote':
        md_content = llm_service.generate_quote(
            db, tenant.id, request.project_description, request.client_info, request.extra_context, request.template_id
        )
    elif request.document_type == 'technical_memo':
        md_content = llm_service.generate_technical_memo(
            db, tenant.id, request.project_description, request.client_info, request.extra_context, request.template_id
        )
    else:
        raise HTTPException(status_code=400, detail="Type de document inconnu")

    # 3. Rendu HTML (avec branding du tenant)
    branding = {
        "primary_color": tenant.primary_color,
        "logo_url": tenant.logo_url
    }
    html_content = doc_service.render_html(md_content, title=request.title, branding=branding)

    # 4. Sauvegarde en base
    doc = create_document(
        db, tenant_id=tenant.id, user_id=current_user.id,
        document_type=request.document_type, title=request.title,
        project_description=request.project_description, client_info=request.client_info,
        extra_context=request.extra_context,
        raw_markdown=md_content, generated_html=html_content
    )

    # 5. Mise à jour du quota (en background)
    tenant.current_month_usage += 1
    db.commit()

    return doc

@router.get("/list", response_model=List[DocumentOut])
def get_my_documents(
    skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    return list_documents(db, tenant_id=current_user.tenant_id, skip=skip, limit=limit)

@router.get("/{doc_id}/html")
def get_document_html(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(verify_token)):
    doc = get_document(db, doc_id, current_user.tenant_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return {"html": doc.generated_html, "markdown": doc.raw_markdown}

@router.get("/{doc_id}/pdf")
def get_document_pdf(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(verify_token)):
    doc = get_document(db, doc_id, current_user.tenant_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    if not doc.pdf_path:
        filename = f"doc_{doc_id}_{uuid.uuid4().hex}.pdf"
        pdf_path = generate_pdf_lite(doc.generated_html, filename)
        doc.pdf_path = pdf_path
        db.commit()
    
    return FileResponse(path=doc.pdf_path, filename=f"{doc.title}.pdf", media_type="application/pdf")

@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(verify_token)):
    doc = get_document(db, doc_id, current_user.tenant_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    db.delete(doc)
    db.commit()
    return {"detail": "Document supprimé"}
