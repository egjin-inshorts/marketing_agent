# Marketing Research Agent

AI 기반 마케팅 리서치 자동화 도구

Google Gemini API와 RAG(Retrieval-Augmented Generation)를 활용하여 시장 트렌드 분석, 경쟁사 동향 조사, 마케팅 인사이트 도출을 자동화합니다. 사내 문서를 기반으로 맥락에 맞는 리서치 결과를 생성하고, 시간에 따른 변화를 추적합니다.

## 주요 기능

- **RAG 기반 리서치**: 사내 문서(제품 정보, 경쟁사 분석 등)를 벡터 DB에 저장하고, 리서치 시 관련 컨텍스트를 자동으로 참조
- **버전 관리**: 리서치 결과를 ID별로 관리하며, 시간에 따른 변화 추적
- **Semantic Diff**: 임베딩 기반 의미론적 비교로 단순 텍스트 변경과 실제 의미 변화를 구분
- **TXT 내보내기**: 리서치 버전 또는 버전 간 diff를 TXT 파일로 내보내기

## 사전 요구사항

- **Conda**: Anaconda 또는 Miniconda 설치 필요
- **Gemini API Key**: [Google AI Studio](https://aistudio.google.com/)에서 API 키 발급

## 설치

```bash
# 1. 환경 세팅 (conda 환경 생성)
bash setup.sh
conda activate marketing-research

# 2. .env 파일 생성 (API 키 설정)
cp .env.example .env
# .env 파일을 열어 GEMINI_API_KEY를 실제 API 키로 변경

# 3. 샘플 문서로 RAG DB 초기화
python cli.py --mode ingest --docs sample_docs/*.txt
```

## 사용법

### 워크플로우

1. **ingest**: 사내 문서를 RAG 벡터 DB에 저장 (최초 1회 또는 문서 추가 시)
2. **research**: 새로운 리서치 시작 (research_id로 관리)
3. **update**: 기존 리서치 업데이트 (이전 결과 기반으로 변경사항 분석)
4. **diff**: 두 버전 간 의미론적 비교
5. **list**: 리서치 히스토리 파일의 버전 목록 확인

### CLI 명령어

#### 문서 추가 (ingest)
```bash
python cli.py --mode ingest --docs /path/to/documents/*.txt
```
- `--docs`: 추가할 문서 경로 (glob 패턴 지원)

#### 초기 리서치 (research)
```bash
python cli.py --mode research \
  --query "2025년 마케팅 자동화 시장 트렌드" \
  --id marketing_automation_2025
```
- `--query`: 리서치 질문
- `--id`: 리서치 고유 ID (버전 관리에 사용, 영문/숫자/밑줄/하이픈만 허용)

#### 리서치 업데이트 (update)
```bash
python cli.py --mode update \
  --query "마케팅 자동화 최신 동향" \
  --id marketing_automation_2025
```
이전 리서치 결과를 참조하여 변경사항(Delta)을 포함한 업데이트 생성

#### 버전 비교 (diff)
```bash
python cli.py --mode diff \
  --id marketing_automation_2025 \
  --old 1 --new 2
```
- `--old`, `--new`: 비교할 버전 번호

#### 버전 목록 확인 (list)
```bash
python cli.py --mode list --file research_history/marketing_automation_2025.json
```
- `--file`: 리서치 히스토리 JSON 파일 경로

출력 예시:
```
File: research_history/marketing_automation_2025.json
Research ID: marketing_automation_2025
Total versions: 3

Ver   Timestamp                 Query
----------------------------------------------------------------------
1     2026-01-20T12:13:42       2025년 마케팅 자동화 시장 트렌드
2     2026-01-20T14:12:14       2025년 마케팅 자동화 시장 트렌드
3     2026-01-20T14:12:55       마케팅 자동화 최신 동향
```

### TXT 내보내기 (export_txt.py)

리서치 결과를 TXT 파일로 내보내는 별도 스크립트입니다. `config.yaml`의 `paths.research_history` 경로를 사용합니다.

```bash
# 기본 config.yaml 사용
python export_txt.py --mode list --id research_id

# 다른 config 파일 지정
python export_txt.py --mode list --id research_id --config /path/to/config.yaml
```

#### 버전 목록 확인
```bash
python export_txt.py --mode list --id marketing_automation_2025
```
출력 예시:
```
Research ID: marketing_automation_2025
Total versions: 3

Ver   Timestamp                 Query
----------------------------------------------------------------------
1     2026-01-20T12:13:42       2025년 마케팅 자동화 시장 트렌드
2     2026-01-20T14:12:14       2025년 마케팅 자동화 시장 트렌드
3     2026-01-20T14:12:55       마케팅 자동화 최신 동향
```

#### 특정 버전 내보내기
```bash
# 기본 출력 파일명: {research_id}_v{version}.txt
python export_txt.py --mode version --id marketing_automation_2025 --version 1

# 출력 파일 지정
python export_txt.py --mode version --id marketing_automation_2025 -v 2 -o my_report.txt
```

#### Diff 내보내기
```bash
# 기본 출력 파일명: {research_id}_diff_v{old}_v{new}.txt
python export_txt.py --mode diff --id marketing_automation_2025 --old 1 --new 2

# 출력 파일 지정
python export_txt.py --mode diff --id marketing_automation_2025 --old 1 --new 3 -o comparison.txt
```

TXT 내보내기 내용:
- **version 모드**: 메타데이터(ID, 버전, 타임스탬프, 쿼리), 전체 findings, 출처, delta
- **diff 모드**: 양쪽 버전 메타데이터, 변경 요약(+/- 라인 수), unified diff, 양쪽 버전 전체 텍스트

### 출력 예시 (diff)

```
================================================================================
[Semantic Analysis] marketing_automation_2025 (v1 → v2)
================================================================================

전체 유사도: 87.3% (변화량: 0.127)
총 섹션: 5 | 변경됨: 2

변경된 섹션:
[섹션 2] MODIFIED (거리: 0.234)
  Old: 경쟁사 A는 시장점유율 15%를 보유하고 있으며...
  New: 경쟁사 A는 최근 M&A를 통해 시장점유율 23%로 급증...

[섹션 4] ADDED (거리: 2.000)
  New: 신규 진입자 C사가 저가 전략으로 시장에 진입...

================================================================================
[Textual Diff] marketing_automation_2025 (v1 → v2)
================================================================================
- 경쟁사 A는 시장점유율 15%를 보유
+ 경쟁사 A는 최근 M&A를 통해 시장점유율 23%로 급증
...
```

## 디렉토리 구조

```
.
├── cli.py                # CLI 엔트리포인트
├── export_txt.py         # TXT 내보내기 스크립트
├── core/
│   ├── agent.py          # MarketingResearchAgent 클래스
│   └── commons.py        # 공통 유틸리티 (config, research I/O)
├── config.yaml           # RAG 설정 및 프롬프트 템플릿
├── sample_docs/          # RAG용 샘플 문서
│   ├── product_overview.txt
│   └── competitors.txt
├── chroma_db/            # RAG 벡터 DB (자동 생성)
├── research_history/     # 리서치 버전 관리 (자동 생성)
│   └── {research_id}.json
├── .env.example          # 환경 변수 템플릿
└── .env                  # API 키 (직접 생성, .env.example 복사)
```

## 설정 (config.yaml)

```yaml
paths:
  rag_db: "./chroma_db"              # 벡터 DB 저장 경로
  research_history: "./research_history"  # 리서치 버전 저장 경로

rag:
  chunk_size: 1000    # 문서 분할 크기 (자)
  chunk_overlap: 200  # 청크 간 오버랩
  top_k: 5            # 검색 결과 개수

prompts:
  research_initial: |  # 초기 리서치 프롬프트 ({rag_context}, {query} 사용)
    ...
  research_update: |   # 업데이트 프롬프트 ({rag_context}, {query}, {previous_research} 사용)
    ...
```

## Python API

```python
from core.agent import MarketingResearchAgent

agent = MarketingResearchAgent()

# 문서 추가
agent.ingest_documents(["docs/product.txt", "docs/market.txt"])

# 리서치 실행
result = agent.research(
    query="2025년 마케팅 자동화 시장 트렌드",
    research_id="marketing_2025",
    update_mode=False  # True면 이전 결과 기반 업데이트
)
print(result["findings"])

# Semantic Diff
diff_result = agent.semantic_diff(
    findings1="이전 리서치 내용...",
    findings2="새 리서치 내용...",
    threshold=0.15  # 변화 감지 임계값
)
print(f"유사도: {diff_result['overall_similarity']:.1%}")
print(f"변경 섹션: {len(diff_result['changed_sections'])}개")
```

## Semantic Diff 상세

### 반환값 구조

```python
{
    "overall_similarity": 0.873,        # 전체 유사도 (0~1)
    "semantic_change_score": 0.127,     # 변화량 (0~2, 0=동일)
    "changed_sections": [
        {
            "section": 2,               # 섹션 번호
            "type": "modified",         # "added" | "removed" | "modified"
            "distance": 0.234,          # 임베딩 거리
            "old": "이전 내용...",
            "new": "새 내용..."
        }
    ],
    "total_sections": 5
}
```

### 거리 해석

| 거리 | 의미 |
|------|------|
| 0.0 | 완전 동일 |
| 0.15 | 경미한 변화 (기본 threshold) |
| 0.3+ | 중대한 의미 변화 |
| 2.0 | 완전 직교 (빈 텍스트 포함) |

### 튜닝

```python
# 민감하게 (작은 변화도 감지)
agent.semantic_diff(f1, f2, threshold=0.10)

# 둔감하게 (큰 변화만 감지)
agent.semantic_diff(f1, f2, threshold=0.25)
```

**Chunk Size 조정**: `core/agent.py`의 `_chunk_findings` 메서드에서 `chunk_size` 파라미터 수정

**임베딩 모델 변경**: `core/agent.py`의 `__init__`에서 `model_name` 수정
```python
self.embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L12-v2"  # 더 빠른 모델
)
```

## 성능 지표

| 텍스트 길이 | 처리 시간 | 메모리 |
|------------|----------|--------|
| ~1K chars  | ~0.5s    | ~50MB  |
| ~5K chars  | ~1.2s    | ~80MB  |
| ~10K chars | ~2.5s    | ~120MB |

*HuggingFace MiniLM 기준, GPU 미사용*
