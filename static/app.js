const AGENT_LABELS = {
  value: "가치투자",
  quant: "퀀트",
  macro: "매크로",
  chart: "차트",
  risk: "리스크",
  behavioral: "행동경제학",
};
const AGENT_ICONS = {
  value: "💰",
  quant: "📐",
  macro: "🌐",
  chart: "📈",
  risk: "🛡️",
  behavioral: "🧠",
};
const AGENT_ORDER = ["value", "quant", "macro", "chart", "risk", "behavioral"];

const VERDICT_CONFIG = {
  매수: { emoji: "🟢", tone: "good" },
  관망: { emoji: "🟡", tone: "warning" },
  매도: { emoji: "🔴", tone: "critical" },
};

const METRIC_LABELS = {
  per: "PER",
  pbr: "PBR",
  roe: "ROE",
  eps: "EPS",
  operating_margin: "영업이익률",
  debt_to_equity: "부채비율",
  return_1m: "1개월 수익률",
  return_3m: "3개월 수익률",
  return_6m: "6개월 수익률",
  return_1y: "1년 수익률",
  beta: "베타",
  std_dev: "변동성(연환산)",
  mdd: "최대낙폭(MDD)",
  "moving_averages.current_price": "현재가",
  "moving_averages.ma5": "5일 이평선",
  "moving_averages.ma20": "20일 이평선",
  "moving_averages.ma60": "60일 이평선",
  "moving_averages.ma120": "120일 이평선",
  "moving_averages.position_vs_ma20": "20일선 대비",
  "moving_averages.position_vs_ma60": "60일선 대비",
  "rsi.rsi": "RSI",
  "rsi.signal": "RSI 신호",
  "macd.macd": "MACD",
  "macd.signal_line": "MACD 시그널",
  "macd.histogram": "MACD 히스토그램",
  "macd.cross": "MACD 크로스",
  "bollinger_bands.upper": "볼린저 상단",
  "bollinger_bands.mid": "볼린저 중단",
  "bollinger_bands.lower": "볼린저 하단",
  "bollinger_bands.position": "볼린저밴드 위치",
  "interest_rates.fed_funds_rate": "미국 기준금리",
  "interest_rates.treasury_10y": "10년물 국채금리",
  "dollar_index.dxy": "달러인덱스(DXY)",
  "fear_greed.score": "Fear & Greed 지수",
  "fear_greed.rating": "시장 심리",
  "news_sentiment.sentiment_score": "뉴스 감성 점수",
  "news_sentiment.summary": "뉴스 감성 요약",
};

const PERCENT_KEYS = new Set([
  "roe",
  "operating_margin",
  "return_1m",
  "return_3m",
  "return_6m",
  "return_1y",
  "std_dev",
  "mdd",
]);

const form = document.getElementById("analyze-form");
const submitBtn = document.getElementById("submit-btn");
const progressSection = document.getElementById("progress-section");
const progressList = document.getElementById("progress-list");
const errorSection = document.getElementById("error-section");
const errorMessage = document.getElementById("error-message");
const resultSection = document.getElementById("result-section");

let pipelineOrder = [];
let currentReportText = "";
let eventSource = null;

async function loadPipeline() {
  try {
    const res = await fetch("/api/pipeline");
    const data = await res.json();
    pipelineOrder = Object.entries(data);
  } catch (err) {
    pipelineOrder = [];
  }
}
loadPipeline();

function verdictConfig(verdict) {
  return VERDICT_CONFIG[verdict] || { emoji: "⚪", tone: "warning" };
}

function formatValue(key, value) {
  if (typeof value === "boolean") return value ? "예" : "아니오";
  if (typeof value === "number") {
    const scaled = PERCENT_KEYS.has(key) ? value * 100 : value;
    const rounded = Math.round(scaled * 100) / 100;
    return PERCENT_KEYS.has(key) ? `${rounded}%` : `${rounded}`;
  }
  return String(value);
}

function flattenEvidence(data, prefix = "") {
  const rows = [];
  Object.entries(data || {}).forEach(([key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    if (value && typeof value === "object" && !Array.isArray(value)) {
      rows.push(...flattenEvidence(value, path));
    } else if (value !== null && value !== undefined && value !== "" && key !== "note") {
      rows.push([path, key, value]);
    }
  });
  return rows;
}

function renderEvidence(evidence) {
  const rows = flattenEvidence(evidence);
  if (rows.length === 0) {
    return `<p class="evidence-empty">근거로 사용할 데이터를 가져오지 못했습니다.</p>`;
  }
  return rows
    .map(([path, key, value]) => {
      const label = METRIC_LABELS[path] || METRIC_LABELS[key] || path;
      return `<div class="evidence-row"><span class="evidence-key">${label}</span><span class="evidence-value">${formatValue(
        key,
        value
      )}</span></div>`;
    })
    .join("");
}

function resetUI() {
  errorSection.classList.add("hidden");
  resultSection.classList.add("hidden");
  progressSection.classList.remove("hidden");
  progressList.innerHTML = pipelineOrder
    .map(
      ([node, label], idx) =>
        `<li data-node="${node}" class="${idx === 0 ? "active" : ""}"><span class="progress-check"></span><span>${label}</span></li>`
    )
    .join("");
}

function markNodeDone(node) {
  const items = Array.from(progressList.children);
  const item = progressList.querySelector(`li[data-node="${node}"]`);
  if (!item) return;
  item.classList.add("done");
  item.classList.remove("active");
  item.querySelector(".progress-check").textContent = "✓";

  const nextPending = items.find((li) => !li.classList.contains("done"));
  if (nextPending) nextPending.classList.add("active");
}

function renderOpinions(opinions, evidence) {
  const grid = document.getElementById("opinions-grid");
  grid.innerHTML = "";
  AGENT_ORDER.forEach((key) => {
    const op = opinions[key];
    if (!op) return;
    const cfg = verdictConfig(op.verdict);
    const card = document.createElement("div");
    card.className = `opinion-card tone-${cfg.tone}`;
    card.innerHTML = `
      <div class="opinion-header">
        <span class="opinion-agent"><span class="opinion-icon">${AGENT_ICONS[key] || ""}</span>${
      AGENT_LABELS[key] || key
    }</span>
        <span class="badge badge-${cfg.tone}">${cfg.emoji} ${op.verdict || "-"}</span>
      </div>
      <div class="meter-track"><div class="meter-fill" style="width:${Math.max(
        0,
        Math.min(100, op.score ?? 0)
      )}%"></div></div>
      <p class="opinion-reason">${op.reason || "-"}</p>
      ${op.detail ? `<p class="opinion-detail">${op.detail}</p>` : ""}
      ${
        op.worst_case
          ? `<p class="opinion-detail">⚠ 최악 시나리오: ${op.worst_case}</p>`
          : ""
      }
      ${
        op.market_emotion
          ? `<p class="opinion-detail">시장 심리: ${op.market_emotion}</p>`
          : ""
      }
      ${op.error ? `<p class="opinion-error">⚠️ LLM 호출 실패로 기본값이 사용됨: ${op.error}</p>` : ""}
      <details>
        <summary class="evidence-toggle">근거 데이터</summary>
        <div class="evidence-list">${renderEvidence(evidence[key] || {})}</div>
      </details>
    `;
    grid.appendChild(card);
  });
}

function renderResult(data) {
  const cfg = verdictConfig(data.final_verdict);
  const verdictCard = document.getElementById("verdict-card");
  verdictCard.className = `card section verdict-card tone-${cfg.tone}`;

  document.getElementById("verdict-emoji").textContent = cfg.emoji;
  document.getElementById("verdict-label").textContent = data.final_verdict || "-";
  document.getElementById("verdict-meta").innerHTML =
    `<span>신뢰도 <b>${data.confidence || "-"}</b></span>` +
    `<span>가중 평균 점수 <b>${(data.final_score ?? 0).toFixed(1)}</b> / 100</span>`;
  document.getElementById("verdict-reason").textContent = data.final_reason || "";

  const dissentingWrap = document.getElementById("dissenting-wrap");
  if (data.dissenting_opinion) {
    dissentingWrap.classList.remove("hidden");
    document.getElementById("dissenting-text").textContent = data.dissenting_opinion;
  } else {
    dissentingWrap.classList.add("hidden");
  }

  const dataErrorNote = document.getElementById("data-error-note");
  if (data.data_error) {
    dataErrorNote.classList.remove("hidden");
    dataErrorNote.textContent = `일부 데이터 수집에 실패했지만 분석을 계속했습니다: ${data.data_error}`;
  } else {
    dataErrorNote.classList.add("hidden");
  }

  renderOpinions(data.opinions || {}, data.evidence || {});

  currentReportText = data.report || "";
  document.getElementById("report-text").textContent = currentReportText;

  progressSection.classList.add("hidden");
  resultSection.classList.remove("hidden");
}

function showError(message) {
  progressSection.classList.add("hidden");
  errorSection.classList.remove("hidden");
  errorMessage.textContent = message;
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  if (eventSource) {
    eventSource.close();
  }

  const ticker = document.getElementById("ticker").value.trim();
  const companyName = document.getElementById("company_name").value.trim();
  const question = document.getElementById("question").value.trim();

  if (!ticker) {
    showError("종목 코드를 입력해주세요.");
    return;
  }

  resetUI();
  submitBtn.disabled = true;
  submitBtn.textContent = "분석 중...";

  const params = new URLSearchParams({ ticker, company_name: companyName, question });
  eventSource = new EventSource(`/api/analyze/stream?${params.toString()}`);

  eventSource.addEventListener("progress", (e) => {
    const payload = JSON.parse(e.data);
    markNodeDone(payload.node);
  });

  eventSource.addEventListener("result", (e) => {
    const payload = JSON.parse(e.data);
    renderResult(payload);
    eventSource.close();
    submitBtn.disabled = false;
    submitBtn.textContent = "분석 시작";
  });

  eventSource.addEventListener("error", (e) => {
    let message = "분석 중 오류가 발생했습니다.";
    if (e.data) {
      try {
        message = JSON.parse(e.data).message || message;
      } catch (_) {
        // ignore parse failure, use default message
      }
    }
    showError(message);
    eventSource.close();
    submitBtn.disabled = false;
    submitBtn.textContent = "분석 시작";
  });
});

document.getElementById("download-btn").addEventListener("click", () => {
  const ticker = document.getElementById("ticker").value.trim() || "report";
  const blob = new Blob([currentReportText], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${ticker}_stockmind_report.md`;
  a.click();
  URL.revokeObjectURL(url);
});
