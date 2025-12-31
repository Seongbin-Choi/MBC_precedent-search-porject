# 3_build_db.py
import sqlite3
import re
from pathlib import Path
from lxml import etree

CONTENT_DIR = Path("data/content")
DB_PATH = Path("data/prec.db")

# 필드 매핑
FIELDS = [
    ("판례정보일련번호", "doc_id", "INTEGER PRIMARY KEY"),
    ("사건명", "case_name", "TEXT"),
    ("사건번호", "case_number", "TEXT"),
    ("선고일자", "judgment_date", "TEXT"),
    ("선고", "judgment", "TEXT"),
    ("법원명", "court_name", "TEXT"),
    ("법원종류코드", "court_type_code", "TEXT"),
    ("사건종류명", "case_type", "TEXT"),
    ("사건종류코드", "case_type_code", "TEXT"),
    ("판결유형", "judgment_type", "TEXT"),
    ("판시사항", "holding", "TEXT"),
    ("판결요지", "summary", "TEXT"),
    ("참조조문", "ref_statutes", "TEXT"),
    ("참조판례", "ref_cases", "TEXT"),
    ("판례내용", "content", "TEXT"),
]

TAG_PATTERN = re.compile(r"<br ?/?>", re.IGNORECASE)


def parse_xml(filepath: Path) -> dict | None:
    """XML 파싱"""
    try:
        text = filepath.read_text(encoding="utf-8")
        root = etree.fromstring(text.encode())

        row = {}
        for kor, eng, dtype in FIELDS:
            elem = root.find(kor)
            val = elem.text.strip() if elem is not None and elem.text else ""
            val = TAG_PATTERN.sub("\n", val)  # <br> → 개행

            # INTEGER 타입 필드는 int로 변환
            if "INTEGER" in dtype:
                row[eng] = int(val) if val else 0
            else:
                row[eng] = val

        return row
    except Exception as e:
        print(f"[ERR] {filepath.name}: {e}")
        return None


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 메인 테이블 생성
    cols = ", ".join(f"{eng} {dtype}" for _, eng, dtype in FIELDS)
    cur.execute(f"DROP TABLE IF EXISTS prec")
    cur.execute(f"CREATE TABLE prec ({cols})")

    # FTS5 가상 테이블 생성 (한글 검색용)
    fts_cols = ", ".join(eng for _, eng, _ in FIELDS if eng != "doc_id")
    cur.execute(f"DROP TABLE IF EXISTS prec_fts")
    cur.execute(f"""
        CREATE VIRTUAL TABLE prec_fts USING fts5(
            {fts_cols},
            content='prec',
            content_rowid='doc_id',
            tokenize='unicode61'
        )
    """)

    # 데이터 삽입
    files = list(CONTENT_DIR.glob("*.xml"))
    print(f"처리 대상: {len(files)}건")

    insert_cols = ", ".join(eng for _, eng, _ in FIELDS)
    placeholders = ", ".join("?" for _ in FIELDS)

    batch = []
    seen_ids = set()
    skipped = 0

    for i, f in enumerate(files, 1):
        row = parse_xml(f)
        if row:
            doc_id = row['doc_id']
            # 중복 체크
            if doc_id in seen_ids:
                skipped += 1
                continue
            seen_ids.add(doc_id)
            batch.append(tuple(row[eng] for _, eng, _ in FIELDS))

        if len(batch) >= 1000:
            cur.executemany(f"INSERT INTO prec ({insert_cols}) VALUES ({placeholders})", batch)
            conn.commit()
            print(f"  {i}/{len(files)} 삽입됨 (중복 제외: {skipped}건)")
            batch = []

    if batch:
        cur.executemany(f"INSERT INTO prec ({insert_cols}) VALUES ({placeholders})", batch)

    print(f"총 중복 제외: {skipped}건")

    # FTS 인덱스 빌드
    print("FTS 인덱스 빌드 중...")
    cur.execute("INSERT INTO prec_fts(prec_fts) VALUES('rebuild')")

    conn.commit()
    conn.close()
    print(f"완료: {DB_PATH}")


if __name__ == "__main__":
    main()
