# 2_download_content.py
import requests
import time
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===== 설정 =====
OC = "qlsqls97"  # 1_download_list.py와 동일한 OC값
LIST_DIR = Path("data/list")
CONTENT_DIR = Path("data/content")
CONTENT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://www.law.go.kr/DRF/lawService.do"
MAX_WORKERS = 3  # 동시 요청 수 (너무 높이면 차단될 수 있음)


def extract_serial_numbers(list_dir: Path) -> list[int]:
    """목록 XML에서 판례일련번호 추출"""
    pattern = re.compile(r"<판례일련번호>(\d+)</판례일련번호>")
    serials = []

    for f in sorted(list_dir.glob("*.xml")):
        text = f.read_text(encoding="utf-8")
        serials.extend(int(m) for m in pattern.findall(text))

    return list(set(serials))  # 중복 제거


def fetch_content(serial: int) -> tuple[int, str | None]:
    """판례 본문 다운로드"""
    output_file = CONTENT_DIR / f"{serial}.xml"
    if output_file.exists():
        return serial, "skip"

    try:
        params = {"OC": OC, "target": "prec", "type": "XML", "ID": serial}
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        output_file.write_text(resp.text, encoding="utf-8")
        return serial, "ok"
    except Exception as e:
        return serial, f"err: {e}"


def main():
    serials = extract_serial_numbers(LIST_DIR)
    print(f"다운로드 대상: {len(serials)}건")

    done = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_content, s): s for s in serials}

        for future in as_completed(futures):
            serial, status = future.result()
            done += 1
            if status != "skip":
                print(f"[{done}/{len(serials)}] {serial}: {status}")

            time.sleep(0.1)  # 약간의 딜레이


if __name__ == "__main__":
    main()
