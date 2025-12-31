# 1_download_list.py
import requests
import time
import re
from pathlib import Path

# ===== 설정 =====
OC = "qlsqls97"  # 발급받은 OC값 입력 (이메일 ID 부분)
OUTPUT_DIR = Path("data/list")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://www.law.go.kr/DRF/lawSearch.do"
DISPLAY = 100  # 한 페이지당 최대 100건


def fetch_page(page: int) -> str:
    """한 페이지 목록 가져오기"""
    params = {
        "OC": OC,
        "target": "prec",
        "type": "XML",
        "display": DISPLAY,
        "page": page,
        "sort": "ddes",  # 선고일자 내림차순 (기본값)
    }
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.text


def get_total_count(xml_text: str) -> int:
    """전체 건수 파싱"""
    match = re.search(r"<totalCnt>(\d+)</totalCnt>", xml_text)
    return int(match.group(1)) if match else 0


def main():
    print(f"OC: {OC}")
    print(f"저장 경로: {OUTPUT_DIR.absolute()}")
    
    # 1페이지로 전체 건수 확인
    print("1페이지 조회 중...")
    first_page = fetch_page(1)
    total = get_total_count(first_page)
    
    if total == 0:
        print("전체 건수를 가져오지 못했습니다. OC값을 확인하세요.")
        print(f"응답 미리보기: {first_page[:500]}")
        return
    
    total_pages = (total + DISPLAY - 1) // DISPLAY
    print(f"전체 판례: {total:,}건, 총 {total_pages:,} 페이지")

    # 1페이지 저장
    (OUTPUT_DIR / "page_0001.xml").write_text(first_page, encoding="utf-8")
    print(f"[OK] 1/{total_pages}")

    # 나머지 페이지 다운로드
    for page in range(2, total_pages + 1):
        output_file = OUTPUT_DIR / f"page_{page:04d}.xml"
        
        if output_file.exists():
            print(f"[SKIP] {page}/{total_pages}")
            continue

        try:
            xml = fetch_page(page)
            output_file.write_text(xml, encoding="utf-8")
            print(f"[OK] {page}/{total_pages}")
        except Exception as e:
            print(f"[ERR] {page}: {e}")

        time.sleep(0.3)  # API 부하 방지

    print("목록 다운로드 완료!")


if __name__ == "__main__":
    main()