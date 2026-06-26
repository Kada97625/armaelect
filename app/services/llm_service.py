from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from sqlalchemy.orm import Session
from app.config import get_settings
from app.crud import get_templates_by_tenant

class LLMService:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.default_llm_model,
            temperature=0.2,
            api_key=settings.openai_api_key if settings.openai_api_key else None
        )

    def get_prompt(self, db: Session, tenant_id: int, doc_type: str, custom_template_id: int = None):
        """
        Récupère le prompt système spécifique au tenant/slug, ou utilise le prompt par défaut.
        """
        # Si un template ID est spécifié
        if custom_template_id:
            from app.models import Template
            tpl = db.query(Template).filter(Template.id == custom_template_id, Template.tenant_id == tenant_id).first()
            if tpl and tpl.system_prompt_override:
                return tpl.system_prompt_override
        
        # Sinon cherche le template par défaut pour ce type
        templates = get_templates_by_tenant(db, tenant_id, doc_type)
        for t in templates:
            if t.is_default and t.system_prompt_override:
                return t.system_prompt_override
        
        return None

    def _call_llm(self, system_prompt: str, user_content: str) -> str:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ]
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            # Fallback simple si l'API LLM tombe
            return f"ERREUR DE GENERATION LLM: {str(e)}"

    def generate_quote(self, db: Session, tenant_id: int, description: str, client_info: str, context: str = None, template_id: int = None) -> str:
        custom_prompt = self.get_prompt(db, tenant_id, 'quote', template_id)
        
        system_prompt = custom_prompt or """Tu es un expert en chiffrage et rédaction de devis dans le domaine de l'installation électrique (Bâtiment, Industrie, Tertiaire).
Ta tâche est de générer un devis professionnel, structuré et détaillé au format Markdown.

RÈGLES STRICTES :
1. L'en-tête doit contenir un numéro de devis (format DEV-XXXX), la date du jour, et les infos client.
2. Le corps principal DOIT être un tableau Markdown avec les colonnes : N°, Désignation des travaux, Qté, Unité, Prix Unitaire H.T., Total H.T.
3. À la fin du tableau, affiche les totaux : Total H.T., TVA (20%), et Total T.T.C.
4. Ajoute une section "Conditions générales" (délais, validité du devis 3 mois, conditions de règlement).
5. Si une information manque pour estimer un poste, fais une estimation réaliste du marché et note-la entre parenthèses (Estimation).
6. Réponds UNIQUEMENT avec le contenu Markdown du devis. Aucun texte d'explication avant ou après."""

        user_content = f"""**Informations Client :** {client_info}

**Description du Projet :**
{description}

**Contexte additionnel :** {context if context else 'Non spécifié'}

Génère le devis complet au format Markdown ci-dessous :"""

        return self._call_llm(system_prompt, user_content)

    def generate_technical_memo(self, db: Session, tenant_id: int, description: str, client_info: str, scope: str = None, template_id: int = None) -> str:
        custom_prompt = self.get_prompt(db, tenant_id, 'technical_memo', template_id)
        
        system_prompt = custom_prompt or """Tu es un ingénieur électricien senior et rédacteur de mémoires techniques.
Ta tâche est de rédiger un mémoire technique professionnel et exhaustif au format Markdown pour un appel d'offres ou un dossier de consultation.

RÈGLES STRICTES :
1. Structure obligatoire avec les sections Markdown (# ## ###) suivantes :
   - 1. Présentation du projet
   - 2. Description technique des travaux
   - 3. Normes et réglementations appliquées (NF C 15-100, etc.)
   - 4. Méthodologie d'exécution et organisation du chantier
   - 5. Matériaux et équipements proposés
   - 6. Planning prévisionnel (sous forme de tableau Markdown)
   - 7. Mesures de sécurité et d'hygiène
   - 8. Gestion des déchets et environnement
2. Le contenu doit être précis, technique et adapté au projet décrit.
3. Réponds UNIQUEMENT avec le contenu Markdown du mémoire. Aucun texte d'explication avant ou après."""

        user_content = f"""**Maître d'Ouvrage :** {client_info}

**Description du projet :**
{description}

**Périmètre spécifique à détailler :** {scope if scope else 'Tous les lots électriques'}

Rédige le mémoire technique complet au format Markdown ci-dessous :"""

        return self._call_llm(system_prompt, user_content)

# Singleton
llm_service = LLMService()