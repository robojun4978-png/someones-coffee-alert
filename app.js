const $ = (s) => document.querySelector(s);
let allItems = [];
let activeTab = "grant";
const today = new Date(); today.setHours(0,0,0,0);
const fmt = (s) => s ? s.replaceAll("-", ".") : "원문 확인";
const daysUntil = (s) => {
  if (!s || !/^\d{4}-\d{2}-\d{2}$/.test(s)) return null;
  const d = new Date(`${s}T00:00:00+09:00`);
  return Math.ceil((d - today) / 86400000);
};
function showList() {
  $("#list-view").hidden = false; $("#detail-view").hidden = true;
  const rows = allItems.filter(x => x.type === activeTab)
    .sort((a,b) => (a.deadline || "9999").localeCompare(b.deadline || "9999"));
  $("#count").textContent = `${rows.length}건`;
  const host = $("#items"); host.innerHTML = "";
  if (!rows.length) {
    host.innerHTML = '<div class="empty">이번 주에는 해당 사업이 없어요</div>';
    return;
  }
  rows.forEach(x => {
    const button = document.createElement("button");
    button.className = "item";
    const title = document.createElement("span"); title.className = "item-title";
    title.textContent = x.title || "사업명 원문 확인";
    if (x.isNew) { const b=document.createElement("span"); b.className="badge new"; b.textContent="NEW"; title.append(b); }
    const d = daysUntil(x.deadline);
    if (d !== null && d >= 0 && d <= 7) { const b=document.createElement("span"); b.className="badge urgent"; b.textContent="마감 임박"; title.append(b); }
    const date = document.createElement("span"); date.className="deadline";
    date.textContent = `마감일: ${fmt(x.deadline)}`;
    button.append(title,date); button.addEventListener("click",()=>showDetail(x)); host.append(button);
  });
}
function showDetail(x) {
  $("#list-view").hidden = true; $("#detail-view").hidden = false;
  $("#d-title").textContent = x.title || "원문 확인";
  $("#d-kind").textContent = x.kind || (x.type==="loan"?"무이자 대출":"지원사업·지원금");
  $("#d-deadline").textContent = fmt(x.deadline);
  $("#d-amount").textContent = x.amount || "원문 확인";
  $("#d-summary").textContent = (x.summary || "자세한 지원 내용과 신청 조건은 공고 원문에서 확인해 주세요.").slice(0,220);
  $("#d-priority").hidden = !x.priority;
  $("#d-interest").hidden = !x.effectiveZero;
  const apply=$("#apply"), source=$("#source");
  apply.href = x.applyUrl || x.url || "#";
  source.href = x.url || x.applyUrl || "#";
  apply.style.display = (x.applyUrl || x.url) ? "flex" : "none";
  source.style.display = (x.url || x.applyUrl) ? "flex" : "none";
  window.scrollTo(0,0);
}
document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>{
  activeTab=b.dataset.tab;
  document.querySelectorAll(".tab").forEach(t=>t.classList.toggle("active",t===b));
  showList();
}));
$("#back").addEventListener("click",showList);
async function start(){
  try {
    const r=await fetch("./data/items.json",{cache:"no-store"});
    if(!r.ok) throw new Error("data unavailable");
    const data=await r.json(); allItems=Array.isArray(data.items)?data.items:[];
    $("#updated").textContent=`마지막 업데이트: ${data.updatedAt || "날짜 확인 중"}`;
  } catch(e) {
    $("#items").innerHTML='<div class="empty">자료를 불러오지 못했어요.<br>잠시 후 다시 열어 주세요.</div>';
    $("#updated").textContent="마지막 업데이트: 이전 자료 확인 필요";
  }
  showList();
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js").catch(()=>{});
}
start();
