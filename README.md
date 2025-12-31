# 판례 검색 시스템

법제처 공공데이터 API를 활용한 판례 검색 시스템

## 개요
약 17만 건의 판례를 수집하여 전문 검색이 가능한 웹 기반 검색 시스템입니다.

## 기능
- 키워드 전문 검색 (FTS5)
- 사건종류 및 판결유형 필터링
- 페이지네이션 (20건/페이지)
- 판례 전문 보기

## 기술 스택
- Python 3.x
- SQLite3 (FTS5)
- Streamlit
- requests, lxml

## 설치 및 실행

### 1. 환경 설정
```bash
pip install -r requirements.txt
```

### 2. 데이터 수집
```bash
# 1단계: 판례 목록 수집 (약 1-2시간)
python 1_download_list.py

# 2단계: 판례 본문 수집 (약 2-3시간)
python 2_download_content.py

# 3단계: DB 구축 (약 10-20분)
python 3_build_db.py
```

### 3. 웹 서비스 실행
```bash
streamlit run 4_app.py
```

브라우저에서 `http://localhost:8501` 접속

## 프로젝트 구조
```
├── 1_download_list.py      # 판례 목록 수집
├── 2_download_content.py   # 판례 본문 수집
├── 3_build_db.py           # DB 구축
├── 4_app.py                # Streamlit 웹 UI
├── requirements.txt        # 패키지 목록
├── data/
│   ├── list/              # 목록 XML 파일
│   ├── content/           # 본문 XML 파일
│   └── prec.db            # SQLite 데이터베이스
```

## 데이터
- **수집 데이터**: 169,751건
- **DB 저장**: 122,598건 (중복 제외)
- **데이터 출처**: 법제처 공공데이터 API

## 주의사항
- 데이터 수집 시 법제처 API 인증키(OC) 필요
- `1_download_list.py` 파일에서 OC 값 설정 필요
- 전체 수집에 약 3-4시간 소요

## 라이선스
MIT License
