#!/usr/bin/env python3
"""썸원스커피 맞춤형 소상공인 지원사업·정책자금 수집기 (기업마당 API + 대전·전국 핵심 상시공고 통합)"""
import os
import json
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, date, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/items.json"
KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST)
TODAY = NOW.date()
BIZ_KEY = os.getenv("BIZINFO_KEY", "").strip()
BIZ_URL = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"

# 2026년 썸원스커피(대전 중구 유천동 · 일반음식점/커피숍 · 영업 8년차 · 연매출 약 2천만 원) 맞춤 검증 공고
CURATED_ITEMS = [
    {
        "id": "PBLN_000000000117908",
        "type": "grant",
        "title": "2026년 소상공인 경영안정 바우처 지원사업 (고정비 25만 원)",
        "kind": "지원금·바우처 (소상공인시장진흥공단)",
        "deadline": "2026-12-31",
        "amount": "최대 25만 원 (전기·가스·수도요금, 4대 보험료 등)",
        "summary": "연매출 1억 400만 원 미만 영세 소상공인에게 전기·가스·수도요금, 4대 보험료, 차량 연료비 등 고정비 납부용 바우처 25만 원을 지원합니다. (연매출 2천만 원 카페 신청 가능)",
        "url": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000117908",
        "applyUrl": "https://voucher.sbiz24.kr/",
        "priority": True,
        "effectiveZero": False,
        "isNew": False,
        "verified": True,
        "source": "기업마당·소상공인24",
    },
    {
        "id": "PBLN_000000000118004",
        "type": "grant",
        "title": "[대전] 2026년 자영업닥터제 운영 (점포 환경개선·1:1 컨설팅)",
        "kind": "경영환경 개선 (대전광역시·대전일자리경제진흥원)",
        "deadline": "예산 소진 시까지",
        "amount": "전문가 1:1 경영컨설팅 및 점포 환경개선비 지원",
        "summary": "대전 소재 소상공인·자영업자 점포에 전문 컨설턴트가 방문해 1:1 맞춤 진단을 제공하고, 컨설팅 이수 점포의 시설·경영환경 개선 비용을 지원합니다.",
        "url": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000118004",
        "applyUrl": "https://www.djbea.or.kr/mps/bizTskPbnc?menuKey=TOfnnvp207",
        "priority": True,
        "effectiveZero": False,
        "isNew": False,
        "verified": True,
        "source": "기업마당·대전일자리경제진흥원",
    },
    {
        "id": "PBLN_000000000120506",
        "type": "grant",
        "title": "[대전] 소상공인·자영업자 재기지원사업 (컨설팅·경영개선)",
        "kind": "경영개선 지원 (대전광역시·대전일자리경제진흥원)",
        "deadline": "예산 소진 시까지",
        "amount": "맞춤형 경영개선 컨설팅 및 판로·마케팅 지원",
        "summary": "대전 지역 소상공인·자영업자를 대상으로 경영진단, 마케팅·세무 컨설팅 및 경영정상화 프로그램을 지원합니다.",
        "url": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000120506",
        "applyUrl": "https://www.djbea.or.kr/mps/bizTskPbnc?menuKey=TOfnnvp207",
        "priority": True,
        "effectiveZero": False,
        "isNew": False,
        "verified": True,
        "source": "기업마당·대전일자리경제진흥원",
    },
    {
        "id": "PBLN_000000000117915",
        "type": "grant",
        "title": "[대전] 2026년 소상공인 온라인 판로·홍보 지원사업",
        "kind": "홍보·판로 지원 (대전광역시·대전일자리경제진흥원)",
        "deadline": "예산 소진 시까지",
        "amount": "온라인 홍보·콘텐츠 제작·플랫폼 입점 지원",
        "summary": "대전 지역 소상공인의 온라인 홍보, 상세페이지·홍보영상 제작, 스마트스토어 및 배달 플랫폼 판로 확대를 지원합니다.",
        "url": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000117915",
        "applyUrl": "https://www.djbea.or.kr/mps/bizTskPbnc?menuKey=TOfnnvp207",
        "priority": False,
        "effectiveZero": False,
        "isNew": False,
        "verified": True,
        "source": "기업마당·대전일자리경제진흥원",
    },
    {
        "id": "PBLN_000000000117737",
        "type": "grant",
        "title": "[대전] 2026년 소상공인 인건비 지원사업 공고",
        "kind": "인건비 지원 (대전광역시·대전일자리경제진흥원)",
        "deadline": "2026-11-30",
        "amount": "근로자 1인당 총 150만 원 (월 50만 원 × 3개월)",
        "summary": "대전 소재 소상공인이 18세 이상 근로자를 신규 채용하고 3개월 이상 고용을 유지한 경우, 근로자 1인당 150만 원의 인건비를 지원합니다.",
        "url": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000117737",
        "applyUrl": "https://www.djbea.or.kr/mps/bizTskPbnc?menuKey=TOfnnvp207",
        "priority": False,
        "effectiveZero": False,
        "isNew": False,
        "verified": True,
        "source": "기업마당·대전일자리경제진흥원",
    },
    {
        "id": "DJJUNGGU_2026_46404",
        "type": "loan",
        "title": "[대전 중구] 2026년 중구 소상공인 특례보증 (이자·보증료 지원)",
        "kind": "특례보증·이차보전 (대전 중구청·대전신용보증재단)",
        "deadline": "예산 소진 시까지",
        "amount": "대출 이자 차액(이차보전) 및 보증수수료 지원",
        "summary": "대전 중구(유천동 포함)에서 3개월 이상 영업 중인 소상공인을 대상으로 대전신용보증재단 특례보증서 발급과 대출이자·보증료를 지원해 이자 부담을 대폭 낮춰줍니다.",
        "url": "https://www.djjunggu.go.kr/prog/saeolGosi/GOSI/sub03_06/view.do?notAncmtMgtNo=46404",
        "applyUrl": "https://www.djsinbo.or.kr/user/boardList.do?boardId=NOTICE&id=homepage_050100000000",
        "priority": True,
        "effectiveZero": False,
        "isNew": False,
        "verified": True,
        "source": "대전 중구청·대전신용보증재단",
    },
    {
        "id": "PBLN_000000000117223",
        "type": "loan",
        "title": "[대전] 2026년 소상공인 초저금리 특별자금 (연 2.7% 이자 지원)",
        "kind": "초저금리 이차보전 (대전광역시·대전신용보증재단)",
        "deadline": "예산 소진 시까지",
        "amount": "최대 7천만 원 한도, 2년간 연 2.7% 이자 대전시 지원",
        "summary": "대전 소재 소상공인에게 업체당 최대 7천만 원 이내 대출에 대해 대출금리 중 연 2.7% 이자를 2년간 대전광역시가 지원합니다. (13개 협약은행 및 카카오뱅크 신청)",
        "url": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000117223",
        "applyUrl": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000117223",
        "priority": True,
        "effectiveZero": False,
        "isNew": False,
        "verified": True,
        "source": "기업마당·대전신용보증재단",
    },
    {
        "id": "SEMAS_2026_POLICY_LOAN",
        "type": "loan",
        "title": "2026년 소상공인 정책자금 (일반경영안정자금·저금리 대환대출)",
        "kind": "소상공인 정책자금 (소상공인시장진흥공단)",
        "deadline": "예산 소진 시까지",
        "amount": "업체당 최대 7천만 원 (저금리 융자 및 고금리 대환)",
        "summary": "일반음식점·커피숍 등 업력 무관 소상공인을 위한 저금리 일반경영안정자금 및 연 7% 이상 고금리 대출을 저금리로 바꿔주는 대환대출입니다.",
        "url": "https://www.sbiz24.kr/landing/",
        "applyUrl": "https://ols.semas.or.kr/",
        "priority": True,
        "effectiveZero": False,
        "isNew": False,
        "verified": True,
        "source": "소상공인시장진흥공단",
    },
]


def clean(s):
    return re.sub(r"<[^>]+>", " ", str(s or "")).replace("&nbsp;", " ").strip()


def get_text(d, *keys):
    for k in keys:
        v = d.get(k)
        if v not in (None, ""):
            return clean(v)
    return ""


def parse_deadline(raw_str):
    """신청기간 문자열에서 종료일(YYYY-MM-DD)을 추출하거나 상시/예산소진 여부를 판별합니다."""
    s = clean(raw_str)
    if not s:
        return "예산 소진 시까지"
    # '2026-01-01 ~ 2026-12-31' 형태면 뒤쪽(마감일)을 기준으로 파싱
    if "~" in s:
        s = s.split("~")[-1].strip()
    # YYYY-MM-DD, YYYY.MM.DD, YYYY년 MM월 DD일
    matches = re.findall(r"(20\d{2})[./년-]\s*(\d{1,2})[./월-]\s*(\d{1,2})", s)
    if matches:
        y, m, d = map(int, matches[-1])
        try:
            return date(y, m, d).isoformat()
        except ValueError:
            pass
    # YYYYMMDD 8자리 숫자
    m8 = re.findall(r"\b(20\d{2})(\d{2})(\d{2})\b", s)
    if m8:
        y, m, d = map(int, m8[-1])
        try:
            return date(y, m, d).isoformat()
        except ValueError:
            pass
    if any(k in s for k in ["예산", "상시", "수시", "별도", "소진"]):
        return "예산 소진 시까지"
    return "원문 확인"


def normalize_url(u, pblanc_id=""):
    u = clean(u)
    if u.startswith("/"):
        return "https://www.bizinfo.go.kr" + u
    if u.startswith("http://") or u.startswith("https://"):
        return u
    if pblanc_id:
        return f"https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId={pblanc_id}"
    return "https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do"


def fetch_bizinfo():
    if not BIZ_KEY:
        print("BIZINFO_KEY 미설정: 기본 검증 공고 목록을 사용합니다.")
        return []
    q = urllib.parse.urlencode({"crtfcKey": BIZ_KEY, "dataType": "json", "searchCnt": "200"})
    req = urllib.request.Request(
        BIZ_URL + "?" + q,
        headers={"User-Agent": "SomeonesCoffeeSupportAlert/1.1"},
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read()
    try:
        obj = json.loads(raw.decode("utf-8-sig"))
    except Exception:
        root = ET.fromstring(raw)
        obj = [
            {child.tag.split("}")[-1]: child.text or "" for child in node}
            for node in root.iter()
            if list(node)
        ]
    if isinstance(obj, list):
        return obj

    def find_list(o):
        if isinstance(o, list):
            return o
        if isinstance(o, dict):
            for v in o.values():
                got = find_list(v)
                if got:
                    return got
        return []

    return find_list(obj)


def classify_biz(row):
    pblanc_id = get_text(row, "pblancId", "id")
    title = get_text(row, "pblancNm", "title", "사업명", "bizTitle")
    if not title:
        return None
    body = get_text(row, "bsnsSumryCn", "description", "사업개요", "summary", "suptTrgt")
    target = get_text(row, "trgetNm", "지원대상", "target", "reqstTrgt")
    org = get_text(row, "jrsdInsttNm", "소관부처", "excInsttNm", "수행기관")
    tags = get_text(row, "hashTags", "pldirSportRealmLclasCodeNm", "pldirSportRealmMlsfcCodeNm")
    text = " ".join([title, body, target, org, tags]).lower()

    # 명백히 해당하지 않는 업종/대상 제외
    banned = [
        "제조업 전용",
        "도소매업 전용",
        "예비창업자 전용",
        "창업 3년 이내",
        "창업 3년이내",
        "법인 전용",
        "수출기업 전용",
        "농업인 전용",
        "어업인 전용",
        "청년 전용",
    ]
    if any(x in text for x in banned):
        return None

    # 타 지자체 전용 공고 제외 (대전이 포함되지 않으면서 타 시도명이 제목/기관에 명시된 경우)
    other_regions = [
        "[서울", "[부산", "[대구", "[인천", "[광주", "[울산", "[세종",
        "[경기", "[강원", "[충북", "[충남", "[전북", "[전남", "[경북", "[경남", "[제주",
        "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시",
        "울산광역시", "세종특별자치시", "경기도", "강원특별자치도", "충청북도",
        "충청남도", "전북특별자치도", "전라남도", "경상북도", "경상남도", "제주특별자치도",
    ]
    if "대전" not in text and any(r in (title + " " + org) for r in other_regions):
        return None

    # 소상공인·자영업·일반점포 관련 키워드 확인
    elig_keywords = [
        "소상공인", "자영업", "소기업", "음식점", "외식", "카페", "점포",
        "골목상권", "전통시장", "개인사업자", "경영안정", "바우처", "특례보증", "이차보전",
    ]
    if not any(x in text for x in elig_keywords):
        return None

    raw_period = get_text(
        row,
        "reqstBeginEndDe",
        "reqstDt",
        "reqstEndDe",
        "reqstEndDt",
        "applicationEndDate",
        "endDate",
        "접수마감일",
    )
    deadline = parse_deadline(raw_period)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", deadline):
        if date.fromisoformat(deadline) < TODAY:
            return None

    loan_keywords = ["융자", "대출", "특례보증", "이차보전", "초저금리", "보증지원", "정책자금", "경영안정자금"]
    is_loan = any(k in (title + " " + tags + " " + body) for k in loan_keywords)
    item_type = "loan" if is_loan else "grant"
    effective_zero = is_loan and any(k in text for k in ["무이자", "금리 0%", "실질 0%", "전액 지원"])

    priority = any(
        x in text
        for x in ["연매출 3억", "매출액 3억", "1억 400", "영세 소상공인", "중구", "음식점"]
    )
    url = normalize_url(get_text(row, "pblancUrl", "detailUrl", "url", "공고URL"), pblanc_id)
    raw_apply = get_text(row, "reqstUrl", "applyUrl", "사업신청URL")
    apply_url = normalize_url(raw_apply, pblanc_id) if raw_apply else url
    amount = get_text(row, "suptAmt", "supportAmount", "지원금액") or "공고 원문 확인"
    summary_text = body[:180] if body else "신청 대상과 세부 지원 조건은 아래 공고 원문 보기 버튼을 눌러 확인해 주세요."

    return {
        "id": pblanc_id or title,
        "type": item_type,
        "title": title,
        "kind": ("무이자·이자지원 대출" if is_loan else "지원사업·지원금") + (f" ({org})" if org else ""),
        "deadline": deadline,
        "amount": amount,
        "summary": summary_text,
        "url": url,
        "applyUrl": apply_url,
        "priority": priority,
        "effectiveZero": effective_zero,
        "isNew": False,
        "verified": True,
        "source": org or "기업마당",
    }


def load_manual():
    p = ROOT / "data/manual_items.json"
    try:
        items = json.loads(p.read_text("utf-8")).get("items", [])
    except Exception:
        return []
    out = []
    for x in items:
        if not x.get("verified"):
            continue
        if x.get("type") not in ("grant", "loan"):
            continue
        if not x.get("title") or not x.get("url"):
            continue
        out.append(x)
    return out


def main():
    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text("utf-8"))
        except Exception:
            old = {}

    collected = []
    try:
        rows = fetch_bizinfo()
        collected = [x for x in (classify_biz(r) for r in rows) if x]
        print(f"기업마당 API 필터링 통과: {len(collected)}건")
    except Exception as e:
        print(f"기업마당 API 호출 경고 (기본 검증 공고로 대체): {e}")

    # 수동 등록 공고 및 2026년 썸원스커피 맞춤 핵심 공고 병합
    collected += load_manual()
    collected += [dict(item) for item in CURATED_ITEMS]

    unique = {}
    for x in collected:
        if x["id"] not in unique:
            unique[x["id"]] = x

    items = list(unique.values())
    previous_ids = {x.get("id") for x in old.get("items", [])}
    for x in items:
        x["isNew"] = bool(previous_ids) and (x.get("id") not in previous_ids)

    items.sort(key=lambda x: x.get("deadline") if re.match(r"^\d{4}-\d{2}-\d{2}$", str(x.get("deadline", ""))) else "9998-12-31")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {"updatedAt": NOW.strftime("%Y-%m-%d %H:%M KST"), "items": items},
            ensure_ascii=False,
            indent=2,
        ),
        "utf-8",
    )
    print(f"최종 저장 완료: 총 {len(items)}건 (지원금 {sum(1 for i in items if i['type']=='grant')}건, 대출 {sum(1 for i in items if i['type']=='loan')}건)")


if __name__ == "__main__":
    main()
