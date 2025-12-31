# 4_app.py
import sqlite3
import streamlit as st
from pathlib import Path

DB_PATH = Path("data/prec.db")


@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data
def get_case_types():
    """사건종류 목록 가져오기"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT case_type FROM prec WHERE case_type != '' ORDER BY case_type")
    return [row[0] for row in cur.fetchall()]


@st.cache_data
def get_judgment_types():
    """판결유형 목록 가져오기"""
    conn = get_connection()
    cur = conn.cursor()
    # judgment 대신 judgment_type 사용
    cur.execute("SELECT DISTINCT judgment_type FROM prec WHERE judgment_type != '' AND judgment_type != 'null' ORDER BY judgment_type")
    results = [row[0] for row in cur.fetchall()]
    return results


def search(query: str, case_type_filter: list = None, judgment_filter: list = None, limit: int = 100):
    conn = get_connection()
    cur = conn.cursor()

    # 기본 쿼리
    if query:
        sql = """
            SELECT p.doc_id, p.case_name, p.case_number, p.judgment_date,
                   p.court_name, p.case_type, p.holding, p.summary, p.judgment_type
            FROM prec p
            JOIN prec_fts ON p.doc_id = prec_fts.rowid
            WHERE prec_fts MATCH ?
        """
        params = [query]

        # 필터 추가 (테이블 alias p 사용)
        if case_type_filter:
            placeholders = ",".join("?" * len(case_type_filter))
            sql += f" AND p.case_type IN ({placeholders})"
            params.extend(case_type_filter)

        if judgment_filter:
            placeholders = ",".join("?" * len(judgment_filter))
            sql += f" AND p.judgment_type IN ({placeholders})"
            params.extend(judgment_filter)

        sql += " ORDER BY p.judgment_date DESC LIMIT ?"
        params.append(limit)
    else:
        sql = """
            SELECT doc_id, case_name, case_number, judgment_date,
                   court_name, case_type, holding, summary, judgment_type
            FROM prec
            WHERE 1=1
        """
        params = []

        # 필터 추가
        if case_type_filter:
            placeholders = ",".join("?" * len(case_type_filter))
            sql += f" AND case_type IN ({placeholders})"
            params.extend(case_type_filter)

        if judgment_filter:
            placeholders = ",".join("?" * len(judgment_filter))
            sql += f" AND judgment_type IN ({placeholders})"
            params.extend(judgment_filter)

        sql += " ORDER BY judgment_date DESC LIMIT ?"
        params.append(limit)

    cur.execute(sql, params)
    return cur.fetchall()


def get_detail(doc_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM prec WHERE doc_id = ?", (doc_id,))
    row = cur.fetchone()
    if row:
        cols = [desc[0] for desc in cur.description]
        return dict(zip(cols, row))
    return None


# ===== UI =====
st.set_page_config(page_title="판례 검색", layout="wide")
st.title("판례 검색")

# 세션 스테이트 초기화
if 'show_detail' not in st.session_state:
    st.session_state.show_detail = {}
if 'results_per_page' not in st.session_state:
    st.session_state.results_per_page = 20

# 검색어 입력
query = st.text_input("", placeholder="ex)공직자 부정청탁", label_visibility="collapsed")

# 필터 영역
col1, col2 = st.columns(2)

with col1:
    case_types = get_case_types()
    selected_case_types = st.multiselect(
        "사건종류",
        options=case_types,
        default=None,
        placeholder="민사, 형사 등"
    )

with col2:
    judgment_types = get_judgment_types()
    selected_judgments = st.multiselect(
        "판결유형",
        options=judgment_types,
        default=None,
        placeholder="판결, 결정, 상고 등"
    )

# 검색 실행
if st.button("Search") or query:
    results = search(
        query,
        case_type_filter=selected_case_types if selected_case_types else None,
        judgment_filter=selected_judgments if selected_judgments else None,
        limit=500  # 최대 500건
    )

    st.markdown(f"**{len(results)}**건의 검색 결과")

    # 페이지네이션
    results_per_page = st.session_state.results_per_page
    total_pages = (len(results) - 1) // results_per_page + 1

    if total_pages > 1:
        page = st.selectbox("페이지", range(1, total_pages + 1), key="page_select")
    else:
        page = 1

    start_idx = (page - 1) * results_per_page
    end_idx = min(start_idx + results_per_page, len(results))

    st.markdown("---")

    # 검색 결과 표시 (현재 페이지만)
    for idx, row in enumerate(results[start_idx:end_idx], start_idx + 1):
        doc_id, case_name, case_number, jdate, court, case_type, holding, summary, judgment_type = row

        # 결과 항목
        st.markdown(f"### {idx}. {case_name}")

        # 메타 정보
        meta_info = f"**{case_number}** | {court}"
        if case_type:
            meta_info += f" | {case_type}"
        if judgment_type:
            meta_info += f" | {judgment_type}"
        if jdate:
            meta_info += f" | {jdate}"
        st.markdown(meta_info)

        # 판시사항 및 판결요지
        if holding:
            with st.expander("판시사항 보기"):
                st.text(holding)

        if summary:
            st.markdown(f"**요지:** {summary[:200]}..." if len(summary) > 200 else f"**요지:** {summary}")

        # 전문 보기 (토글 방식)
        detail_key = f"detail_{doc_id}"
        if detail_key not in st.session_state.show_detail:
            st.session_state.show_detail[detail_key] = False

        if st.button("전문 보기" if not st.session_state.show_detail[detail_key] else "전문 숨기기", key=f"btn_{doc_id}"):
            st.session_state.show_detail[detail_key] = not st.session_state.show_detail[detail_key]
            st.rerun()

        if st.session_state.show_detail.get(detail_key, False):
            detail = get_detail(doc_id)
            if detail and detail.get("content"):
                st.markdown("---")
                st.markdown("**판례내용 전문:**")
                st.text(detail["content"])

        st.markdown("---")
