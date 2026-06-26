#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# ARMAELECT - Déploiement Automatique sur Google Cloud Platform
# ═══════════════════════════════════════════════════════════════
# Utilisation : bash deploy.sh
# Prérequis  : gcloud CLI installé et configuré
# ═══════════════════════════════════════════════════════════════

echo "=== 🚀 ARMAELECT - Déploiement GCP ==="

# ── Configuration ──────────────────────────────────────────────
PROJECT_ID="${PROJECT_ID:-armaelect-prod}"
REGION="${REGION:-europe-west1}"
ZONE="${ZONE:-europe-west1-b}"

# ── Étape 1 : Créer / sélectionner le projet ──────────────────
echo "📦 Projet GCP : $PROJECT_ID"
if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
  gcloud projects create "$PROJECT_ID" --name="ARMAELECT"
fi
gcloud config set project "$PROJECT_ID"

# ── Étape 2 : Activer les APIs nécessaires ────────────────────
echo "🔌 Activation des APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  iamcredentials.googleapis.com \
  --quiet

# ── Étape 3 : Créer le dépôt Artifact Registry ────────────────
echo "🗃️  Création Artifact Registry..."
if ! gcloud artifacts repositories describe armaelect --location="$REGION" &>/dev/null; then
  gcloud artifacts repositories create armaelect \
    --repository-format=docker \
    --location="$REGION" \
    --description="Images Docker ARMAELECT"
fi

# ── Étape 4 : Créer l'instance Cloud SQL PostgreSQL ────────────
echo "🐘 Création Cloud SQL..."
if ! gcloud sql instances describe armaelect-db &>/dev/null; then
  gcloud sql instances create armaelect-db \
    --database-version=POSTGRES_14 \
    --region="$REGION" \
    --tier=db-f1-micro \
    --storage-size=10GB \
    --storage-type=SSD \
    --root-password="ChangerMoi123!"
fi

DB_PASS=$(gcloud sql users list --instance=armaelect-db --filter="name=armaelect" --format="value(name)" 2>/dev/null || echo "")
if [ -z "$DB_PASS" ]; then
  gcloud sql users create armaelect --password="ChangerMoi123!" --instance=armaelect-db
fi

# Récupérer le nom de connexion Cloud SQL
CLOUD_SQL_INSTANCE=$(gcloud sql instances describe armaelect-db --format="value(connectionName)")
echo "🌐 Cloud SQL Instance : $CLOUD_SQL_INSTANCE"

# ── Étape 5 : Créer la base de données ────────────────────────
gcloud sql databases create armaelect --instance=armaelect-db --quiet || true

# ── Étape 6 : Créer un compte de service pour Cloud Run ───────
echo "🔑 Création Service Account..."
SA_EMAIL="armaelect-sa@$PROJECT_ID.iam.gserviceaccount.com"
if ! gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
  gcloud iam service-accounts create armaelect-sa \
    --display-name="ARMAELECT Cloud Run SA"
fi

# Donner les droits d'accès à Cloud SQL
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/cloudsql.client" --quiet

# ── Étape 7 : Stocker les secrets dans Secret Manager ──────────
echo "🔒 Création des secrets..."
echo -n "${OPENAI_API_KEY:-sk-placeholder}" | \
  gcloud secrets create openai-api-key --data-file=- --quiet || true
echo -n "${JWT_SECRET:-changez-moi-en-production}" | \
  gcloud secrets create jwt-secret --data-file=- --quiet || true

# Donner accès aux secrets au SA
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor" --quiet || true
gcloud secrets add-iam-policy-binding jwt-secret \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor" --quiet || true

# ── Étape 8 : Lancer le build et le déploiement ────────────────
echo "☁️  Lancement du build Cloud Build..."
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_REGION="$REGION",_CLOUD_SQL_INSTANCE="$CLOUD_SQL_INSTANCE",_OPENAI_KEY="${OPENAI_API_KEY:-sk-placeholder}",_JWT_SECRET="${JWT_SECRET:-changez-moi-en-production}",_DB_PASSWORD="ChangerMoi123!"

# ── Étape 9 : Récupérer l'URL du service ──────────────────────
echo ""
echo "═══════════════════════════════════════════════════"
echo "✅  DÉPLOIEMENT TERMINÉ !"
echo "═══════════════════════════════════════════════════"
gcloud run services describe armaelect --region="$REGION" --format="value(status.url)"
echo ""
echo "⚠️  N'oublie pas de :"
echo "  1. Configurer ton API key OpenAI : gcloud secrets versions add openai-api-key --data-file=-"
echo "  2. Changer le mot de passe PostgreSQL"
echo "  3. Configurer la 1ère connexion admin via init_admin.py dans Cloud Shell"
echo "═══════════════════════════════════════════════════"
