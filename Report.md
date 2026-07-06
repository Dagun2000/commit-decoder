# Project Git Commit Decoder Chronicles

## [2026-07-06 09:07] Commit: #9f8c1f1
* **Author:** Dagun2000
* **Original Message:** `Added pipeline and actual llm`

### 1. What (기능적 요약)
이번 변경은 커밋 분석 도구에 실제 LLM 연동과 end-to-end 파이프라인 실행 기능을 추가한 것이다. 이제 원본 커밋 정보에서 Stage 1 스켈레톤을 추출하고, 이를 바탕으로 Stage 2 한국어 분석 리포트를 생성하는 전체 흐름이 동작한다. 또한 OpenAI와 로컬 Ollama를 선택적으로 사용할 수 있도록 구성되었고, 실행 방법과 환경 설정이 README에 반영되었다.

### 2. How (구현 메커니즘)
`llm_client.py`에 LLM 설정 객체와 설정 오류 처리, 그리고 provider별 클라이언트 생성 로직이 추가되어 환경변수 기반으로 OpenAI/Ollama를 전환한다. `stage1_skeleton.py`는 raw diff를 구조화된 스켈레톤으로 압축하는 전용 프롬프트와 chat-completions 호출을 담당하고, `stage2_report.py`는 이 스켈레톤을 입력으로 최종 분석 문서를 생성하며 빈 스켈레톤일 때는 조기 종료한다. `pipeline.py`는 `extract_commit -> stage1_skeleton -> stage2_report` 순서로 전체 단계를 오케스트레이션하고, 결과를 포맷팅해 출력하는 CLI 진입점 역할을 한다.

### 3. Why (기술적 의도)
핵심 의도는 기존의 플레이스홀더 수준 구현을 실제 사용 가능한 LLM 기반 분석 파이프라인으로 전환하는 데 있다. Stage 1에서 diff를 먼저 압축해 노이즈를 줄임으로써 Stage 2가 더 안정적으로 의도와 구조를 해석하도록 설계한 것으로 보인다. 또한 클라우드 API와 로컬 모델을 모두 지원해 개발 편의성, 비용 통제, 오프라인 실험 가능성을 함께 확보하려는 목적이 반영되어 있다.

---
