#!/bin/bash

echo "Setting up Marketing Research Agent..."

# 디렉토리 생성
mkdir -p sample_docs

# Conda 환경 생성
conda env create -f environment.yaml

echo ""
echo "✓ Environment created. Activate with:"
echo "  conda activate marketing-research"
echo ""
echo "✓ Create .env file and add your credentials:"
echo "  cat > .env << EOF"
echo "GEMINI_API_KEY=your_key_here"
echo "GEMINI_MODEL=gemini-2.0-flash-exp"
echo "EOF"
echo ""
echo "✓ Sample documents are in: ./sample_docs/"
echo ""
echo "✓ Initialize RAG database with sample docs:"
echo "  python cli.py --mode ingest --docs sample_docs/*.txt"
