# Marketing Research Agent

AI 기반 마케팅 리서치 자동화 도구

Google Gemini AI를 활용하여 시장 트렌드 분석, 경쟁사 동향 조사, 마케팅 인사이트를 자동으로 생성합니다. 사내 문서를 참고하여 우리 회사 상황에 맞는 분석 결과를 제공하고, 시간에 따른 변화를 추적할 수 있습니다.

## 목차

- [주요 기능](#주요-기능)
- [시작하기](#시작하기)
- [사용 방법](#사용-방법)
  - [1. 사내 문서 등록](#1-사내-문서-등록)
  - [2. 리서치 실행](#2-리서치-실행)
  - [3. 리서치 업데이트](#3-리서치-업데이트)
  - [4. 버전 비교](#4-버전-비교)
  - [5. 결과 내보내기](#5-결과-내보내기)
- [프롬프트 커스터마이징](#프롬프트-커스터마이징)
- [폴더 구조](#폴더-구조)

## 주요 기능

| 기능 | 설명 |
|------|------|
| **사내 문서 참조** | 제품 정보, 경쟁사 자료 등을 등록하면 AI가 분석 시 자동으로 참고 |
| **버전 관리** | 같은 주제로 여러 번 리서치해도 이력이 자동 저장 |
| **변화 추적** | 이전 리서치와 비교하여 무엇이 달라졌는지 자동 분석 |
| **파일 내보내기** | 결과를 TXT 파일로 저장하여 보고서 작성에 활용 |

## 시작하기

### 준비물

1. **Conda** 설치 ([Miniconda 다운로드](https://docs.conda.io/en/latest/miniconda.html))
2. **Gemini API Key** 발급 ([Google AI Studio](https://aistudio.google.com/)에서 무료 발급)

### 설치 방법

```bash
# 1. 환경 설치
bash setup.sh
conda activate marketing-research

# 2. API 키 설정
cp .env.example .env
# .env 파일을 열어 GEMINI_API_KEY에 발급받은 키 입력

# 3. 샘플 문서로 테스트
python cli.py --mode ingest --docs sample_docs/*.txt
```

## 사용 방법

### 1. 사내 문서 등록

AI가 참고할 문서(제품 소개서, 경쟁사 분석 자료 등)를 등록합니다.

```bash
python cli.py --mode ingest --docs /path/to/documents/*.txt
```

> 💡 문서는 TXT 형식으로 준비해주세요. 한 번 등록하면 이후 모든 리서치에서 자동으로 참고됩니다.

### 2. 리서치 실행

새로운 리서치를 시작합니다.

```bash
python cli.py --mode research \
  --query "2025년 마케팅 자동화 시장 트렌드" \
  --id marketing_trend_2025
```

- `--query`: 분석하고 싶은 주제나 질문
- `--id`: 리서치를 구분하는 이름 (영문, 숫자, 밑줄, 하이픈만 사용)

### 3. 리서치 업데이트

기존 리서치를 최신 정보로 업데이트합니다. 이전 결과와 비교하여 변경사항을 자동으로 분석해줍니다.

```bash
python cli.py --mode update \
  --query "마케팅 자동화 최신 동향" \
  --id marketing_trend_2025
```

### 4. 버전 비교

두 버전 간 어떤 내용이 달라졌는지 비교합니다.

```bash
# 버전 목록 확인
python cli.py --mode list --file research_history/marketing_trend_2025.json

# 버전 1과 2 비교
python cli.py --mode diff --id marketing_trend_2025 --old 1 --new 2
```

**비교 결과 예시:**
```
전체 유사도: 87.3% (변화량: 12.7%)
변경된 섹션: 2개

[섹션 2] 변경됨
  이전: 경쟁사 A는 시장점유율 15%를 보유...
  현재: 경쟁사 A는 M&A를 통해 시장점유율 23%로 급증...

[섹션 4] 새로 추가됨
  현재: 신규 진입자 C사가 저가 전략으로 시장에 진입...
```

### 5. 결과 내보내기

리서치 결과를 TXT 파일로 저장합니다.

```bash
# 특정 버전 내보내기
python export_txt.py --mode version --id marketing_trend_2025 --version 1

# 버전 비교 결과 내보내기
python export_txt.py --mode diff --id marketing_trend_2025 --old 1 --new 2
```

## 프롬프트 커스터마이징

`config.yaml` 파일을 수정하여 AI의 분석 방식과 출력 형식을 원하는 대로 바꿀 수 있습니다.

### 설정 파일 구조

```yaml
prompts:
  research_initial: |    # 새 리서치용 프롬프트
    ...
  research_update: |     # 업데이트용 프롬프트
    ...
```

### 사용 가능한 변수

프롬프트 안에서 아래 변수들이 자동으로 치환됩니다:

| 변수 | 설명 |
|------|------|
| `{rag_context}` | 등록한 사내 문서 내용 |
| `{query}` | 입력한 리서치 질문 |
| `{previous_research}` | 이전 리서치 결과 (업데이트 시에만) |

### 커스터마이징 예시

**영문으로 결과 받기:**
```yaml
prompts:
  research_initial: |
    You are a marketing research expert.

    **Internal Documents:**
    {rag_context}

    **Research Question:** {query}

    Please provide:
    # Key Findings
    # Data & Statistics
    # Actionable Insights
    # Sources
```

**B2B SaaS 분석에 특화:**
```yaml
prompts:
  research_initial: |
    당신은 B2B SaaS 마케팅 전문가입니다.

    **사내 문서:** {rag_context}
    **분석 요청:** {query}

    SaaS 관점(MRR, CAC, LTV 등)에서 분석하고,
    PLG 전략 중심으로 인사이트를 도출하세요.
```

**간단한 요약만 받기:**
```yaml
prompts:
  research_initial: |
    **참고 자료:** {rag_context}
    **질문:** {query}

    3문장 이내로 핵심만 답변하세요.
```

### 프롬프트 작성 팁

1. **역할 부여**: "당신은 ~전문가입니다"로 시작하면 더 전문적인 답변을 얻을 수 있습니다
2. **출력 형식 지정**: 원하는 섹션 구조를 `#` 헤딩으로 명시하면 일관된 형식으로 받을 수 있습니다
3. **구체적 지시**: 포함해야 할 내용, 분석 관점 등을 구체적으로 적어주세요
4. **변수 필수 포함**: `{rag_context}`와 `{query}`는 반드시 포함해야 합니다

## 폴더 구조

```
.
├── cli.py                # 메인 실행 파일
├── export_txt.py         # 결과 내보내기
├── config.yaml           # 설정 파일 (프롬프트 수정은 여기서)
├── sample_docs/          # 샘플 문서
├── chroma_db/            # 문서 저장소 (자동 생성)
└── research_history/     # 리서치 결과 저장 (자동 생성)
```
