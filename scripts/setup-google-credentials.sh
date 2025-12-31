#!/bin/bash
# Setup Google Credentials for Docs2Code Pipeline
# Creates service account and configures OAuth clients

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECRETS_DIR="$PROJECT_ROOT/secrets"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔐 Google Credentials Setup${NC}"
echo "=============================="
echo ""

# Check prerequisites
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found${NC}"
    echo "Install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}⚠️  No default project set${NC}"
    echo -n "Enter Google Cloud Project ID: "
    read -r PROJECT_ID
    gcloud config set project "$PROJECT_ID"
fi

echo -e "${GREEN}✅ Using project: $PROJECT_ID${NC}"
echo ""

# Service account email
SA_NAME="docs2code-svc"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# Menu
echo "What would you like to do?"
echo ""
echo "1) Create service account + key file"
echo "2) Enable required APIs"
echo "3) Show service account email (for Drive sharing)"
echo "4) List existing service accounts"
echo "5) Rotate service account key"
echo "6) Delete service account"
echo "7) Complete setup (1 + 2)"
echo ""
echo -n "Choice [1-7]: "
read -r CHOICE
echo ""

case "$CHOICE" in
    1)
        # Create service account
        echo -e "${BLUE}📝 Creating service account...${NC}"

        if gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
            echo -e "${YELLOW}⚠️  Service account already exists: $SA_EMAIL${NC}"
        else
            gcloud iam service-accounts create "$SA_NAME" \
                --display-name="Docs2Code Pipeline Service Account" \
                --description="Headless automation for Docs→GitHub sync, OCR, scheduled ingestion"

            echo -e "${GREEN}✅ Service account created: $SA_EMAIL${NC}"
        fi

        # Create key file
        mkdir -p "$SECRETS_DIR"

        KEY_FILE="$SECRETS_DIR/docs2code-svc.json"
        if [ -f "$KEY_FILE" ]; then
            echo -e "${YELLOW}⚠️  Key file already exists: $KEY_FILE${NC}"
            echo -n "Overwrite? (y/N): "
            read -r CONFIRM
            if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
                echo "Skipping key creation"
                exit 0
            fi
            mv "$KEY_FILE" "$KEY_FILE.bak.$(date +%s)"
            echo -e "${YELLOW}   Backed up existing key${NC}"
        fi

        gcloud iam service-accounts keys create "$KEY_FILE" \
            --iam-account="$SA_EMAIL"

        echo -e "${GREEN}✅ Key file created: $KEY_FILE${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
        echo "   1. This file contains sensitive credentials"
        echo "   2. It's gitignored - never commit to git"
        echo "   3. Add to GitHub Secrets as GOOGLE_CREDENTIALS"
        echo ""
        echo "To copy key content:"
        echo -e "${BLUE}   cat $KEY_FILE | pbcopy${NC}  # macOS"
        echo -e "${BLUE}   cat $KEY_FILE | xclip -selection clipboard${NC}  # Linux"
        echo ""
        echo -e "${YELLOW}📋 Share Drive files with:${NC}"
        echo -e "${GREEN}   $SA_EMAIL${NC}"
        ;;

    2)
        # Enable APIs
        echo -e "${BLUE}🔌 Enabling required APIs...${NC}"

        APIS=(
            "drive.googleapis.com"
            "docs.googleapis.com"
            "sheets.googleapis.com"
            "vision.googleapis.com"
        )

        for API in "${APIS[@]}"; do
            echo -n "   Enabling $API... "
            if gcloud services enable "$API" 2>/dev/null; then
                echo -e "${GREEN}✓${NC}"
            else
                echo -e "${RED}✗${NC}"
            fi
        done

        echo ""
        echo -e "${GREEN}✅ APIs enabled${NC}"
        ;;

    3)
        # Show service account email
        echo -e "${YELLOW}📋 Service Account Email:${NC}"
        echo ""
        echo -e "${GREEN}   $SA_EMAIL${NC}"
        echo ""
        echo "Share Google Drive folders/files with this email:"
        echo ""
        echo "1. Open Google Drive"
        echo "2. Right-click folder → Share"
        echo "3. Add: $SA_EMAIL"
        echo "4. Set permissions: Viewer or Editor"
        ;;

    4)
        # List service accounts
        echo -e "${BLUE}📋 Service Accounts in $PROJECT_ID:${NC}"
        echo ""
        gcloud iam service-accounts list
        ;;

    5)
        # Rotate key
        echo -e "${BLUE}🔄 Rotating service account key...${NC}"

        # List current keys
        echo "Current keys:"
        gcloud iam service-accounts keys list --iam-account="$SA_EMAIL"
        echo ""

        # Create new key
        mkdir -p "$SECRETS_DIR"
        NEW_KEY="$SECRETS_DIR/docs2code-svc-new.json"

        gcloud iam service-accounts keys create "$NEW_KEY" \
            --iam-account="$SA_EMAIL"

        echo -e "${GREEN}✅ New key created: $NEW_KEY${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Update GitHub Secret: GOOGLE_CREDENTIALS"
        echo "2. Test workflows with new key"
        echo "3. Delete old key:"
        echo ""
        echo -e "${YELLOW}   gcloud iam service-accounts keys delete <KEY_ID> \\\\${NC}"
        echo -e "${YELLOW}     --iam-account=\"$SA_EMAIL\"${NC}"
        ;;

    6)
        # Delete service account
        echo -e "${RED}⚠️  WARNING: This will delete the service account and all keys${NC}"
        echo -n "Are you sure? Type 'DELETE' to confirm: "
        read -r CONFIRM

        if [ "$CONFIRM" != "DELETE" ]; then
            echo "Cancelled"
            exit 0
        fi

        gcloud iam service-accounts delete "$SA_EMAIL" --quiet

        echo -e "${GREEN}✅ Service account deleted${NC}"

        # Clean up local key
        if [ -f "$SECRETS_DIR/docs2code-svc.json" ]; then
            echo -n "Delete local key file too? (y/N): "
            read -r CONFIRM_KEY
            if [[ "$CONFIRM_KEY" =~ ^[Yy]$ ]]; then
                rm "$SECRETS_DIR/docs2code-svc.json"
                echo -e "${GREEN}✅ Local key file deleted${NC}"
            fi
        fi
        ;;

    7)
        # Complete setup
        echo -e "${BLUE}🚀 Complete Setup${NC}"
        echo ""

        # Run options 1 and 2
        bash "$0" <<EOF
1
EOF

        echo ""

        bash "$0" <<EOF
2
EOF

        echo ""
        echo -e "${GREEN}✅ Setup complete!${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Share Drive folders with: $SA_EMAIL"
        echo "2. Add key to GitHub Secrets: GOOGLE_CREDENTIALS"
        echo "3. Configure n8n OAuth (see docs/GOOGLE_CREDENTIALS_SETUP.md)"
        echo "4. Test with: gh workflow run sync-google-docs.yml"
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}📖 Full documentation:${NC}"
echo "   docs/GOOGLE_CREDENTIALS_SETUP.md"
