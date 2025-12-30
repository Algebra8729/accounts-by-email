#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[*] Préparation de l'environnement d'audit...${NC}"
pip install -r requirements.txt

if [ -z "$1" ]; then
    echo -e "${BLUE}[?] Entrez l'adresse e-mail cible : ${NC}"
    read target
else
    target=$1
fi

python3 auditor.py "$target"
```
