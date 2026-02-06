#!/bin/bash

cd "$(dirname "$0")"

echo "==================================="
echo "  Gerador de Prompts para IA"
echo "==================================="

# Verifica se o venv existe, se não, cria e instala
if [ ! -d "backend/venv" ]; then
    echo "Primeira execução - configurando ambiente..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    echo ""
fi

# Ativa o venv
source backend/venv/bin/activate

# Verifica .env
if [ ! -f "backend/.env" ]; then
    echo "ATENÇÃO: Configure backend/.env com OPENAI_API_KEY"
    echo ""
fi

echo "Acesse: http://localhost:8000"
echo "Ctrl+C para parar"
echo ""

cd backend
uvicorn main:app --reload --port 8000
