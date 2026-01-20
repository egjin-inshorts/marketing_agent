# core/agent.py
import sys
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from google import genai
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from difflib import unified_diff
import os
from dotenv import load_dotenv
import numpy as np
import colorama

# Initialize colorama for cross-platform ANSI color support
colorama.init()

from core.commons import (
    load_config,
    get_research_history_path,
    get_rag_db_path,
    load_research,
    save_research,
)


class MarketingResearchAgent:
    def __init__(self, config_path: str = "config.yaml"):
        load_dotenv()
        self.config = load_config(config_path)

        # Gemini client 초기화
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        self.client = genai.Client(api_key=api_key)
        self.model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')

        self.rag_db_path = get_rag_db_path(self.config)
        self.research_history_path = get_research_history_path(self.config)
        self.research_history_path.mkdir(exist_ok=True)

        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.config['rag']['embedding_model']
        )
    
    def ingest_documents(self, doc_paths: List[str]):
        """문서를 RAG DB에 추가 (최신 API)"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config['rag']['chunk_size'],
            chunk_overlap=self.config['rag']['chunk_overlap']
        )
        
        all_chunks = []
        all_metadatas = []
        
        for path in doc_paths:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            chunks = splitter.split_text(text)
            all_chunks.extend(chunks)
            all_metadatas.extend([{"source": path}] * len(chunks))
        
        # Chroma DB 생성/업데이트 (persist 자동 처리)
        Chroma.from_texts(
            texts=all_chunks,
            embedding=self.embeddings,
            metadatas=all_metadatas,
            persist_directory=str(self.rag_db_path)
        )
    
    def _retrieve_context(self, query: str) -> str:
        """RAG 검색"""
        vectorstore = Chroma(
            persist_directory=str(self.rag_db_path),
            embedding_function=self.embeddings
        )
        k = self.config['rag']['top_k']
        docs = vectorstore.similarity_search(query, k=k)
        return "\n\n".join([f"[출처: {doc.metadata['source']}]\n{doc.page_content}" for doc in docs])
    
    def _load_research_version(self, research_id: str) -> Optional[dict]:
        return load_research(research_id, self.research_history_path, raise_if_missing=False)

    def _save_research_version(self, research_id: str, data: dict):
        existing = self._load_research_version(research_id) or {"versions": []}

        new_version = {
            "version": len(existing["versions"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "query": data["query"],
            "findings": data["findings"],
            "sources": data.get("sources", []),
            "delta": data.get("delta", "Initial research")
        }
        existing["versions"].append(new_version)

        save_research(research_id, existing, self.research_history_path)
    
    def _build_prompt(self, template_key: str, **kwargs) -> str:
        template = self.config['prompts'][template_key]
        return template.format(**kwargs)
    
    def research(self, query: str, research_id: str, update_mode: bool = False) -> dict:
        # RAG context
        rag_context = self._retrieve_context(query)
        
        # 이전 리서치 로드
        previous_research = ""
        if update_mode:
            existing = self._load_research_version(research_id)
            if existing and existing["versions"]:
                latest = existing["versions"][-1]
                previous_research = latest['findings']
        
        # Prompt 생성
        if update_mode:
            prompt = self._build_prompt(
                'research_update',
                rag_context=rag_context,
                query=query,
                previous_research=previous_research
            )
        else:
            prompt = self._build_prompt(
                'research_initial',
                rag_context=rag_context,
                query=query
            )
        
        # Gemini API 호출
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            findings = response.text
        except Exception as e:
            print(f"Error: Gemini API call failed: {e}", file=sys.stderr)
            raise RuntimeError(f"Failed to generate research content: {e}") from e
        
        # 결과 저장
        result = {
            "query": query,
            "findings": findings,
            "sources": ["Gemini Web Search"],
            "delta": "Updated with new insights" if update_mode else "Initial research"
        }
        self._save_research_version(research_id, result)
        
        return result
    
    def _chunk_findings(self, findings: str, chunk_size: int = 500):
        """텍스트를 의미 단위로 분할"""
        sentences = findings.replace('\n\n', '\n').split('\n')
        chunks = []
        current_chunk = ""
        
        for sent in sentences:
            if len(current_chunk) + len(sent) < chunk_size:
                current_chunk += sent + "\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sent + "\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _semantic_distance(self, text1: str, text2: str) -> float:
        """두 텍스트 간 임베딩 거리 (0=identical, 2=orthogonal)"""
        if not text1 or not text2:
            return 2.0
        
        emb1 = np.array(self.embeddings.embed_query(text1))
        emb2 = np.array(self.embeddings.embed_query(text2))
        
        # Cosine distance = 1 - cosine_similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2) + 1e-8)
        return 1 - similarity
    
    def semantic_diff(self, findings1: str, findings2: str, threshold: float = 0.15) -> dict:
        """의미론적 변화 분석"""
        # Overall similarity
        overall_dist = self._semantic_distance(findings1, findings2)
        overall_similarity = 1 - overall_dist
        
        # Chunk-level comparison
        chunks1 = self._chunk_findings(findings1)
        chunks2 = self._chunk_findings(findings2)
        
        changed_sections = []
        max_len = max(len(chunks1), len(chunks2))
        
        for i in range(max_len):
            c1 = chunks1[i] if i < len(chunks1) else ""
            c2 = chunks2[i] if i < len(chunks2) else ""
            
            distance = self._semantic_distance(c1, c2)
            
            if distance > threshold:
                change_type = "modified"
                if not c1:
                    change_type = "added"
                elif not c2:
                    change_type = "removed"
                
                changed_sections.append({
                    "section": i + 1,
                    "type": change_type,
                    "distance": round(distance, 3),
                    "old": c1[:100] + "..." if len(c1) > 100 else c1,
                    "new": c2[:100] + "..." if len(c2) > 100 else c2
                })
        
        return {
            "overall_similarity": round(overall_similarity, 3),
            "semantic_change_score": round(overall_dist, 3),
            "changed_sections": changed_sections,
            "total_sections": max_len
        }
    
    def show_diff(self, research_id: str, v1: int, v2: int):
        """두 버전 간 diff 시각화 (textual + semantic)"""
        data = self._load_research_version(research_id)
        if not data or len(data["versions"]) < max(v1, v2):
            print("버전을 찾을 수 없습니다.")
            return
        
        findings1 = data["versions"][v1-1]["findings"]
        findings2 = data["versions"][v2-1]["findings"]
        
        # Semantic Diff
        print(f"\n{'='*80}\n[Semantic Analysis] {research_id} (v{v1} → v{v2})\n{'='*80}")
        semantic_result = self.semantic_diff(findings1, findings2)
        
        print(f"\n전체 유사도: {semantic_result['overall_similarity']:.1%} "
              f"(변화량: {semantic_result['semantic_change_score']:.3f})")
        print(f"총 섹션: {semantic_result['total_sections']} | "
              f"변경됨: {len(semantic_result['changed_sections'])}\n")
        
        if semantic_result['changed_sections']:
            print("변경된 섹션:")
            for change in semantic_result['changed_sections']:
                color = '\033[92m' if change['type'] == 'added' else '\033[91m' if change['type'] == 'removed' else '\033[93m'
                print(f"{color}[섹션 {change['section']}] {change['type'].upper()} "
                      f"(거리: {change['distance']})\033[0m")
                if change['old']:
                    print(f"  Old: {change['old']}")
                if change['new']:
                    print(f"  New: {change['new']}")
                print()
        
        # Textual Diff
        print(f"\n{'='*80}\n[Textual Diff] {research_id} (v{v1} → v{v2})\n{'='*80}")
        findings1_lines = findings1.splitlines(keepends=True)
        findings2_lines = findings2.splitlines(keepends=True)
        
        diff = unified_diff(
            findings1_lines, findings2_lines,
            fromfile=f"Version {v1}",
            tofile=f"Version {v2}",
            lineterm=''
        )
        
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                print(f"\033[92m{line}\033[0m")
            elif line.startswith('-') and not line.startswith('---'):
                print(f"\033[91m{line}\033[0m")
            else:
                print(line)
