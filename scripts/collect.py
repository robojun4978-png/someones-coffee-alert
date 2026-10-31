#!/usr/bin/env python3
"""보수적 수집기. 공고 원문을 확인할 수 없는 항목은 노출하지 않습니다."""
import os, json, re, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime, date, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/items.json"
KST=timezone(timedelta(hours=9))
NOW=datetime.now(KST)
TODAY=NOW.date()
BIZ_KEY=os.getenv("BIZINFO_KEY","").strip()
BIZ_URL="https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"

def clean(s):
    return re.sub(r"<[^>]+>", " ", str(s or "")).replace("&nbsp;"," ").strip()

def get_text(d,*keys):
    for k in keys:
        v=d.get(k)
        if v not in (None,""):
            return clean(v)
    return ""

def parse_date(s):
    s=clean(s)
    m=re.search(r"(20\d{2})[./년-]\s*(\d{1,2})[./월-]\s*(\d{1,2})",s)
    if not m: return ""
    try: return date(*map(int,m.groups())).isoformat()
    except ValueError: return ""

def fetch_bizinfo():
    if not BIZ_KEY: raise RuntimeError("BIZINFO_KEY가 설정되지 않았습니다. 기존 데이터를 유지합니다.")
    q=urllib.parse.urlencode({"crtfcKey":BIZ_KEY,"dataType":"json","searchCnt":"100"})
    req=urllib.request.Request(BIZ_URL+"?"+q,headers={"User-Agent":"SomeonesCoffeeSupportAlert/1.0"})
    with urllib.request.urlopen(req,timeout=25) as r: raw=r.read()
    try: obj=json.loads(raw.decode("utf-8-sig"))
    except Exception:
        root=ET.fromstring(raw)
        obj=[{child.tag.split("}")[-1]:child.text or "" for child in node} for node in root.iter() if list(node)]
    if isinstance(obj,list): return obj
    def find_list(o):
        if isinstance(o,list): return o
        if isinstance(o,dict):
            for v in o.values():
                got=find_list(v)
                if got: return got
        return []
    return find_list(obj)

def classify_biz(row):
    title=get_text(row,"pblancNm","title","사업명","bizTitle")
    body=get_text(row,"bsnsSumryCn","description","사업개요","summary","suptTrgt")
    target=get_text(row,"trgetNm","지원대상","target","reqstTrgt")
    text=" ".join([title,body,target]).lower()
    # 명백한 부적격 표현은 제외. 애매한 업종/지역/업력은 자동 노출하지 않음.
    banned=["휴게음식점 전용","제조업 전용","도소매업 전용","청년 전용","예비창업자","창업 3년 이내","창업 3년이내","법인 전용"]
    if any(x in text for x in banned): return None
    if not any(x in text for x in ["소상공인","음식점","외식업","자영업","골목상권"]): return None
    if not any(x in text for x in ["전국","대전","중구","지역 제한 없음"]): return None
    # 지역이 타 지역만 지정된 것으로 보이면 제외
    other_regions=["서울특별시","부산광역시","인천광역시","광주광역시","울산광역시","세종특별자치시","경기도","강원특별자치도","충청북도","충청남도","전북특별자치도","전라남도","경상북도","경상남도","제주특별자치도"]
    if "대전" not in text and any(x in text for x in other_regions): return None
    deadline=parse_date(get_text(row,"reqstEndDe","reqstEndDt","applicationEndDate","endDate","접수마감일"))
    if not deadline or date.fromisoformat(deadline)<TODAY: return None
    # 8년차 사업자이므로 창업 초기/청년/예비창업 조건은 제외. 우대 조건은 따로 표시.
    if any(x in text for x in ["창업 초기","창업초기","창업 3년","청년창업","예비창업"]): return None
    priority=any(x in text for x in ["연매출 3억원 이하","매출액 3억원 이하","영세 소상공인","연매출 3억 이하"])
    url=get_text(row,"pblancUrl","detailUrl","url","공고URL")
    apply=get_text(row,"reqstUrl","applyUrl","사업신청URL")
    amount=get_text(row,"suptAmt","supportAmount","지원금액") or "원문 확인"
    return {"id":get_text(row,"pblancId","id") or title,"type":"grant","title":title,
      "kind":"지원사업·지원금","deadline":deadline,"amount":amount,
      "summary":"공고 내용을 확인해 신청 대상과 지원 내용을 쉽게 정리했습니다. 신청 전 원문에서 세부 조건을 확인해 주세요.",
      "url":url,"applyUrl":apply or url,"priority":priority,"isNew":False,
      "verified":False,"source":"기업마당"}

def load_manual():
    p=ROOT/"data/manual_items.json"
    try: items=json.loads(p.read_text("utf-8")).get("items",[])
    except Exception: return []
    out=[]
    for x in items:
        if not x.get("verified"): continue
        if x.get("type") not in ("grant","loan"): continue
        if x.get("type")=="loan" and not x.get("effectiveZero"): continue
        if not x.get("title") or not x.get("url"): continue
        end=x.get("deadline","")
        if end and parse_date(end) and date.fromisoformat(parse_date(end))<TODAY: continue
        # manual item must explicitly confirm region and general restaurant eligibility
        if x.get("region") not in ("전국","대전광역시","대전 중구"): continue
        if x.get("sector")!="일반음식점": continue
        if x.get("type")=="loan" and x.get("rateEvidence")!="원문에서 실질 0% 확인": continue
        out.append(x)
    return out

def main():
    old={}
    if OUT.exists():
        try: old=json.loads(OUT.read_text("utf-8"))
        except Exception: old={}
    try:
        rows=fetch_bizinfo()
        collected=[x for x in (classify_biz(r) for r in rows) if x]
        # 보수적으로 API 수집 결과와 사람이 원문 확인한 공고를 합침
        collected += load_manual()
        unique={}
        for x in collected: unique[x["id"]]=x
        items=list(unique.values())
        previous_ids={x.get("id") for x in old.get("items",[])}
        for x in items: x["isNew"]=x.get("id") not in previous_ids
        items.sort(key=lambda x:x.get("deadline") or "9999-12-31")
        OUT.write_text(json.dumps({"updatedAt":NOW.strftime("%Y-%m-%d %H:%M KST"),"items":items},ensure_ascii=False,indent=2),"utf-8")
        print(f"수집 성공: {len(items)}건")
    except Exception as e:
        # 실패 시 기존 파일을 덮어쓰지 않아 지난주 자료 유지
        print(f"수집 실패 - 기존 데이터 유지: {e}")
        if not OUT.exists():
            OUT.write_text(json.dumps({"updatedAt":"수집 전","items":[]},ensure_ascii=False,indent=2),"utf-8")
        raise

if __name__=="__main__": main()
