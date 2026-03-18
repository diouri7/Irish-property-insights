"""
add_heatmap.py
Embeds the interactive Ireland heatmap into the homepage
Run from: C:\\Users\\WAFI\\irish-property-insights
"""
import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

HEATMAP_SECTION = '''
<!-- ── HEATMAP SECTION ── -->
<section style="background:#0a0c0f;padding:5rem 2rem;border-top:1px solid #1a1c20;">
  <div style="max-width:960px;margin:0 auto;">
    <div style="text-align:center;margin-bottom:2.5rem;">
      <div style="display:inline-block;font-size:0.7rem;font-weight:500;letter-spacing:0.18em;text-transform:uppercase;color:#c9a84c;border:1px solid #c9a84c;padding:0.3rem 0.8rem;border-radius:2px;margin-bottom:1.2rem;">Interactive Map</div>
      <h2 style="font-family:\\'Playfair Display\\',serif;font-size:clamp(1.6rem,3.5vw,2.4rem);font-weight:900;color:white;line-height:1.1;margin-bottom:0.8rem;">Irish Property Investment Heatmap</h2>
      <p style="color:#9a9690;font-size:0.95rem;font-weight:300;max-width:500px;margin:0 auto;">Click any county to see yield, growth and risk. County-level overview — full micro-area rankings in the report.</p>
    </div>

    <div style="display:flex;gap:0.4rem;margin-bottom:2rem;justify-content:center;">
      <div style="display:flex;background:#1a1c20;border:1px solid #2a2c30;border-radius:3px;padding:0.3rem;">
        <button onclick="setMetric(\\'yield\\',this)" class="hm-toggle active" style="padding:0.5rem 1.2rem;border:none;border-radius:2px;font-family:inherit;font-size:0.78rem;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;background:#c9a84c;color:#0f1014;">Rental Yield</button>
        <button onclick="setMetric(\\'growth\\',this)" class="hm-toggle" style="padding:0.5rem 1.2rem;border:none;border-radius:2px;font-family:inherit;font-size:0.78rem;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;background:transparent;color:#6b6860;">5yr Growth</button>
        <button onclick="setMetric(\\'risk\\',this)" class="hm-toggle" style="padding:0.5rem 1.2rem;border:none;border-radius:2px;font-family:inherit;font-size:0.78rem;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;background:transparent;color:#6b6860;">Risk Score</button>
      </div>
    </div>

    <div style="display:flex;gap:2.5rem;align-items:flex-start;flex-wrap:wrap;">
      <!-- MAP -->
      <div style="flex:1;min-width:280px;">
        <svg id="ireland-map" viewBox="0 0 370 420" style="width:100%;height:auto;">
          <path id="hm-Donegal"   onclick="hmSelect(\\'Donegal\\')"   style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M90,22 L135,15 L165,30 L178,52 L158,68 L143,83 L120,76 L98,60 L83,45 Z"/>
          <path id="hm-NI" style="fill:#141618;stroke:#0a0c0f;stroke-width:1;" d="M165,30 L218,23 L232,45 L218,68 L188,76 L158,68 L178,52 Z"/>
          <path id="hm-Sligo"     onclick="hmSelect(\\'Sligo\\')"     style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M76,83 L106,76 L120,76 L128,91 L113,106 L90,106 L72,94 Z"/>
          <path id="hm-Leitrim"   onclick="hmSelect(\\'Leitrim\\')"   style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M120,76 L143,83 L147,98 L135,113 L120,109 L113,106 L128,91 Z"/>
          <path id="hm-Mayo"      onclick="hmSelect(\\'Mayo\\')"      style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M38,76 L75,68 L98,60 L98,83 L83,98 L72,94 L60,113 L38,121 L23,106 L30,91 Z"/>
          <path id="hm-Roscommon" onclick="hmSelect(\\'Roscommon\\')" style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M106,106 L128,98 L147,98 L151,117 L140,132 L120,132 L106,124 L102,113 Z"/>
          <path id="hm-Galway"    onclick="hmSelect(\\'Galway\\')"    style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M23,117 L60,113 L83,98 L98,106 L102,113 L106,124 L98,140 L83,158 L60,158 L38,155 L19,140 Z"/>
          <path id="hm-Clare"     onclick="hmSelect(\\'Clare\\')"     style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M60,158 L83,158 L98,140 L109,147 L113,163 L106,178 L86,186 L64,178 L57,166 Z"/>
          <path id="hm-Limerick"  onclick="hmSelect(\\'Limerick\\')"  style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M86,186 L106,178 L120,181 L132,196 L124,211 L106,215 L86,207 L79,196 Z"/>
          <path id="hm-Kerry"     onclick="hmSelect(\\'Kerry\\')"     style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M57,196 L79,196 L86,207 L83,226 L68,243 L49,245 L34,230 L38,211 Z"/>
          <path id="hm-Cork"      onclick="hmSelect(\\'Cork\\')"      style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M83,226 L106,215 L128,215 L147,222 L155,237 L147,252 L128,260 L106,260 L86,252 L72,243 L68,243 Z"/>
          <path id="hm-Tipperary" onclick="hmSelect(\\'Tipperary\\')" style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M109,147 L132,143 L151,151 L162,166 L158,184 L143,192 L132,196 L120,181 L113,163 Z"/>
          <path id="hm-Waterford" onclick="hmSelect(\\'Waterford\\')" style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M128,215 L147,222 L166,215 L173,203 L162,192 L158,184 L143,192 L132,196 Z"/>
          <path id="hm-Wexford"   onclick="hmSelect(\\'Wexford\\')"   style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M166,215 L185,207 L200,215 L204,230 L192,245 L173,249 L155,237 L147,222 Z"/>
          <path id="hm-Kilkenny"  onclick="hmSelect(\\'Kilkenny\\')"  style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M151,151 L170,151 L185,162 L185,181 L173,192 L162,192 L158,184 L162,166 Z"/>
          <path id="hm-Carlow"    onclick="hmSelect(\\'Carlow\\')"    style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M170,151 L189,147 L200,158 L196,173 L185,181 L185,162 Z"/>
          <path id="hm-Laois"     onclick="hmSelect(\\'Laois\\')"     style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M151,117 L173,121 L192,128 L200,143 L189,147 L170,151 L151,151 L140,132 Z"/>
          <path id="hm-Offaly"    onclick="hmSelect(\\'Offaly\\')"    style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M128,106 L151,105 L173,106 L177,121 L173,121 L151,117 L140,124 L128,117 Z"/>
          <path id="hm-Westmeath" onclick="hmSelect(\\'Westmeath\\')" style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M140,85 L166,84 L188,91 L192,106 L177,106 L173,106 L151,105 L140,98 Z"/>
          <path id="hm-Longford"  onclick="hmSelect(\\'Longford\\')"  style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M128,76 L151,74 L166,84 L155,94 L140,98 L140,85 L132,79 Z"/>
          <path id="hm-Cavan"     onclick="hmSelect(\\'Cavan\\')"     style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M147,60 L173,57 L192,64 L196,79 L188,91 L166,84 L151,74 L143,66 Z"/>
          <path id="hm-Monaghan"  onclick="hmSelect(\\'Monaghan\\')"  style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M173,49 L200,45 L215,57 L211,72 L192,75 L192,64 L181,55 Z"/>
          <path id="hm-Meath"     onclick="hmSelect(\\'Meath\\')"     style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M188,91 L215,87 L230,98 L230,117 L211,124 L196,121 L192,106 Z"/>
          <path id="hm-Louth"     onclick="hmSelect(\\'Louth\\')"     style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M211,72 L234,68 L243,83 L234,98 L215,98 L215,87 Z"/>
          <path id="hm-Dublin"    onclick="hmSelect(\\'Dublin\\')"    style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M230,98 L251,94 L260,109 L252,124 L234,128 L230,117 Z"/>
          <path id="hm-Wicklow"   onclick="hmSelect(\\'Wicklow\\')"   style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M234,128 L252,124 L268,136 L264,155 L249,166 L230,162 L222,147 L226,134 Z"/>
          <path id="hm-Kildare"   onclick="hmSelect(\\'Kildare\\')"   style="cursor:pointer;stroke:#0a0c0f;stroke-width:1.5;transition:filter 0.15s;" d="M196,121 L218,117 L230,128 L226,143 L211,147 L200,143 L192,128 Z"/>

          <!-- Labels -->
          <text x="118" y="50" font-size="7" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Donegal</text>
          <text x="97" y="94" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Sligo</text>
          <text x="132" y="98" font-size="5" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Leitrim</text>
          <text x="62" y="102" font-size="7" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Mayo</text>
          <text x="125" y="117" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Roscommon</text>
          <text x="64" y="136" font-size="7" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Galway</text>
          <text x="86" y="168" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Clare</text>
          <text x="105" y="200" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Limerick</text>
          <text x="60" y="222" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Kerry</text>
          <text x="112" y="240" font-size="7" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Cork</text>
          <text x="136" y="170" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Tipperary</text>
          <text x="150" y="207" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Waterford</text>
          <text x="178" y="232" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Wexford</text>
          <text x="170" y="172" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Kilkenny</text>
          <text x="183" y="160" font-size="5" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Carlow</text>
          <text x="170" y="138" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Laois</text>
          <text x="152" y="113" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Offaly</text>
          <text x="163" y="97" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Westmeath</text>
          <text x="147" y="84" font-size="5" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Longford</text>
          <text x="170" y="73" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Cavan</text>
          <text x="194" y="62" font-size="5" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Monaghan</text>
          <text x="210" y="108" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Meath</text>
          <text x="224" y="86" font-size="5" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Louth</text>
          <text x="242" y="112" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Dublin</text>
          <text x="248" y="148" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Wicklow</text>
          <text x="211" y="134" font-size="6" fill="rgba(255,255,255,0.45)" text-anchor="middle" pointer-events="none">Kildare</text>
        </svg>
      </div>

      <!-- SIDEBAR -->
      <div style="width:280px;flex-shrink:0;">
        <div id="hm-county-info">
          <div style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;padding:2rem 1.2rem;text-align:center;color:#4a4845;font-size:0.85rem;line-height:1.6;margin-bottom:1rem;">
            <div style="font-size:1.5rem;margin-bottom:0.8rem;">🗺️</div>
            Click any county to see its investment scores
          </div>
        </div>

        <div style="margin-bottom:1rem;">
          <div style="font-size:0.68rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.5rem;" id="hm-legend-title">Rental Yield</div>
          <div style="height:7px;border-radius:2px;background:linear-gradient(to right,#0d3d22,#1a6b3c,#c9a84c,#d4821a,#c0392b);margin-bottom:0.3rem;"></div>
          <div style="display:flex;justify-content:space-between;font-size:0.68rem;color:#4a4845;" id="hm-legend-labels">
            <span>Low (3%)</span><span>High (8%+)</span>
          </div>
        </div>

        <div style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;overflow:hidden;">
          <div style="padding:0.7rem 1.1rem;font-size:0.68rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;border-bottom:1px solid #2a2c30;" id="hm-ranking-title">Top Counties by Yield</div>
          <div id="hm-ranking-items"></div>
        </div>
      </div>
    </div>
  </div>
</section>

<style>
.hm-toggle { transition: background 0.2s, color 0.2s; }
.hm-county-path-hover:hover { opacity: 0.85; filter: brightness(1.25); stroke: white !important; stroke-width: 2 !important; }
</style>

<script>
const hmData = {
  Dublin:     { yield: 5.5, growth: 5.3, risk: \\'Medium\\', signal: \\'STRONG BUY\\', price: 484581 },
  Cork:       { yield: 5.1, growth: 6.2, risk: \\'Low\\',    signal: \\'STRONG BUY\\', price: 320000 },
  Galway:     { yield: 4.8, growth: 5.8, risk: \\'Low\\',    signal: \\'STRONG BUY\\', price: 285000 },
  Kildare:    { yield: 4.2, growth: 6.8, risk: \\'Low\\',    signal: \\'STRONG BUY\\', price: 355000 },
  Meath:      { yield: 4.5, growth: 7.1, risk: \\'Low\\',    signal: \\'STRONG BUY\\', price: 320000 },
  Wicklow:    { yield: 3.9, growth: 5.5, risk: \\'Low\\',    signal: \\'MODERATE\\',   price: 380000 },
  Limerick:   { yield: 5.4, growth: 6.9, risk: \\'Low\\',    signal: \\'STRONG BUY\\', price: 245000 },
  Waterford:  { yield: 5.2, growth: 5.1, risk: \\'Medium\\', signal: \\'STRONG BUY\\', price: 220000 },
  Louth:      { yield: 5.0, growth: 7.1, risk: \\'Low\\',    signal: \\'STRONG BUY\\', price: 235000 },
  Wexford:    { yield: 4.6, growth: 6.3, risk: \\'Low\\',    signal: \\'STRONG BUY\\', price: 210000 },
  Kilkenny:   { yield: 4.4, growth: 5.8, risk: \\'Low\\',    signal: \\'MODERATE\\',   price: 230000 },
  Tipperary:  { yield: 5.8, growth: 4.2, risk: \\'Medium\\', signal: \\'MODERATE\\',   price: 175000 },
  Clare:      { yield: 5.3, growth: 5.6, risk: \\'Low\\',    signal: \\'STRONG BUY\\', price: 195000 },
  Kerry:      { yield: 4.9, growth: 6.1, risk: \\'Medium\\', signal: \\'STRONG BUY\\', price: 215000 },
  Mayo:       { yield: 6.2, growth: 3.8, risk: \\'Medium\\', signal: \\'MODERATE\\',   price: 145000 },
  Sligo:      { yield: 5.9, growth: 4.1, risk: \\'Medium\\', signal: \\'MODERATE\\',   price: 155000 },
  Donegal:    { yield: 6.5, growth: 3.5, risk: \\'High\\',   signal: \\'MODERATE\\',   price: 125000 },
  Roscommon:  { yield: 6.8, growth: 3.2, risk: \\'High\\',   signal: \\'AVOID\\',      price: 115000 },
  Laois:      { yield: 5.1, growth: 5.9, risk: \\'Low\\',    signal: \\'STRONG BUY\\', price: 185000 },
  Offaly:     { yield: 5.3, growth: 5.2, risk: \\'Medium\\', signal: \\'MODERATE\\',   price: 165000 },
  Westmeath:  { yield: 5.0, growth: 5.4, risk: \\'Low\\',    signal: \\'STRONG BUY\\', price: 175000 },
  Longford:   { yield: 7.1, growth: 2.8, risk: \\'High\\',   signal: \\'AVOID\\',      price: 95000  },
  Cavan:      { yield: 6.1, growth: 3.6, risk: \\'High\\',   signal: \\'AVOID\\',      price: 130000 },
  Monaghan:   { yield: 5.7, growth: 4.0, risk: \\'Medium\\', signal: \\'MODERATE\\',   price: 140000 },
  Carlow:     { yield: 5.2, growth: 6.1, risk: \\'Low\\',    signal: \\'STRONG BUY\\', price: 190000 },
  Leitrim:    { yield: 7.8, growth: 2.5, risk: \\'High\\',   signal: \\'AVOID\\',      price: 85000  },
};

let hmMetric = \\'yield\\';
let hmSelected = null;

function hmColor(name, metric) {
  const d = hmData[name]; if (!d) return \\'#1a1c20\\';
  if (metric === \\'yield\\') {
    const v = d.yield;
    if (v >= 7) return \\'#c0392b\\'; if (v >= 6) return \\'#d4821a\\';
    if (v >= 5.5) return \\'#b8962e\\'; if (v >= 5) return \\'#2d8a5e\\';
    if (v >= 4) return \\'#1a6b3c\\'; return \\'#0d3d22\\';
  }
  if (metric === \\'growth\\') {
    const v = d.growth;
    if (v >= 7) return \\'#1a6b3c\\'; if (v >= 6) return \\'#2d8a5e\\';
    if (v >= 5) return \\'#b8962e\\'; if (v >= 4) return \\'#d4821a\\'; return \\'#c0392b\\';
  }
  if (metric === \\'risk\\') {
    if (d.risk === \\'Low\\') return \\'#1a6b3c\\';
    if (d.risk === \\'Medium\\') return \\'#b8962e\\'; return \\'#c0392b\\';
  }
}

function hmColorMap() {
  Object.keys(hmData).forEach(name => {
    const el = document.getElementById(\\'hm-\\' + name);
    if (el) el.style.fill = hmColor(name, hmMetric);
  });
}

function setMetric(metric, btn) {
  hmMetric = metric;
  document.querySelectorAll(\\'.hm-toggle\\').forEach(b => {
    b.style.background = \\'transparent\\'; b.style.color = \\'#6b6860\\';
  });
  btn.style.background = \\'#c9a84c\\'; btn.style.color = \\'#0f1014\\';
  const titles = { yield: \\'Rental Yield\\', growth: \\'5yr Growth\\', risk: \\'Risk Score\\' };
  const legendLabels = {
    yield: [\\'Low (3%)\\', \\'High (8%+)\\'],
    growth: [\\'Low (2%)\\', \\'High (7%+)\\'],
    risk: [\\'Low Risk\\', \\'High Risk\\']
  };
  document.getElementById(\\'hm-legend-title\\').textContent = titles[metric];
  const ll = legendLabels[metric];
  document.getElementById(\\'hm-legend-labels\\').innerHTML = \\'<span>\\' + ll[0] + \\'</span><span>\\' + ll[1] + \\'</span>\\';
  document.getElementById(\\'hm-ranking-title\\').textContent =
    metric === \\'yield\\' ? \\'Top Counties by Yield\\' :
    metric === \\'growth\\' ? \\'Top Counties by Growth\\' : \\'Lowest Risk Counties\\';
  hmColorMap(); hmRanking();
  if (hmSelected) hmCard(hmSelected);
}

function hmSelect(name) {
  Object.keys(hmData).forEach(n => {
    const el = document.getElementById(\\'hm-\\' + n);
    if (el) { el.style.strokeWidth = \\'1.5\\'; el.style.stroke = \\'#0a0c0f\\'; }
  });
  const sel = document.getElementById(\\'hm-\\' + name);
  if (sel) { sel.style.strokeWidth = \\'2.5\\'; sel.style.stroke = \\'white\\'; }
  hmSelected = name; hmCard(name);
  document.querySelectorAll(\\'.hm-rank-item\\').forEach(i => {
    i.style.background = i.dataset.county === name ? \\'#22252a\\' : \\'transparent\\';
  });
}

function hmCard(name) {
  const d = hmData[name]; if (!d) return;
  const sc = d.signal === \\'STRONG BUY\\' ? \\'rgba(26,107,60,0.3);color:#4ade80\\'
           : d.signal === \\'MODERATE\\' ? \\'rgba(201,168,76,0.2);color:#c9a84c\\'
           : \\'rgba(192,57,43,0.2);color:#ef4444\\';
  const gc = d.growth >= 6 ? \\'#4ade80\\' : d.growth >= 4 ? \\'#c9a84c\\' : \\'#ef4444\\';
  const yc = d.yield >= 5 ? \\'#4ade80\\' : d.yield >= 4 ? \\'#c9a84c\\' : \\'#ef4444\\';
  const rc = d.risk === \\'Low\\' ? \\'#4ade80\\' : d.risk === \\'Medium\\' ? \\'#c9a84c\\' : \\'#ef4444\\';
  const reportCounties = [\\'Dublin\\',\\'Cork\\',\\'Galway\\',\\'Kildare\\',\\'Kerry\\',\\'Meath\\',\\'Wicklow\\'];
  const hasReport = reportCounties.includes(name);
  const ctaHtml = hasReport
    ? \\'<a href="/#reports" style="display:block;text-align:center;padding:0.7rem;background:#c9a84c;color:#0f1014;border-radius:3px;font-size:0.78rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;text-decoration:none;margin-top:0.8rem;">Unlock All Micro-Areas in \\' + name + \\'  — €29 →</a>\\'
    : \\'<a href="/#snap" style="display:block;text-align:center;padding:0.7rem;background:#1a1c20;color:#9a9690;border:1px solid #2a2c30;border-radius:3px;font-size:0.78rem;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;text-decoration:none;margin-top:0.8rem;">Get Free \\' + name + \\'  Snapshot →</a>\\';

  document.getElementById(\\'hm-county-info\\').innerHTML = \\'<div style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;overflow:hidden;margin-bottom:1rem;"><div style="padding:1rem 1.2rem 0.8rem;border-bottom:1px solid #2a2c30;"><div style="font-family:Playfair Display,serif;font-size:1.3rem;font-weight:700;color:white;">\\' + name + \\'</div><div style="display:inline-block;font-size:0.62rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;padding:0.2rem 0.6rem;border-radius:2px;margin-top:0.4rem;background:\\' + sc + \\';">\\' + d.signal + \\'</div></div><div style="display:grid;grid-template-columns:1fr 1fr;"><div style="padding:0.8rem 1.1rem;border-right:1px solid #2a2c30;border-bottom:1px solid #2a2c30;"><div style="font-size:0.62rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.3rem;">Gross Yield</div><div style="font-family:Playfair Display,serif;font-size:1.2rem;font-weight:700;color:\\' + yc + \\';">\\' + d.yield + \\'%</div></div><div style="padding:0.8rem 1.1rem;border-bottom:1px solid #2a2c30;"><div style="font-size:0.62rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.3rem;">5yr Growth</div><div style="font-family:Playfair Display,serif;font-size:1.2rem;font-weight:700;color:\\' + gc + \\';">+\\' + d.growth + \\'%</div></div><div style="padding:0.8rem 1.1rem;border-right:1px solid #2a2c30;"><div style="font-size:0.62rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.3rem;">Risk</div><div style="font-family:Playfair Display,serif;font-size:1.2rem;font-weight:700;color:\\' + rc + \\';">\\' + d.risk + \\'</div></div><div style="padding:0.8rem 1.1rem;"><div style="font-size:0.62rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.3rem;">Median Price</div><div style="font-family:Playfair Display,serif;font-size:1.2rem;font-weight:700;color:white;">€\\' + d.price.toLocaleString() + \\'</div></div></div>\\' + ctaHtml + \\'</div>\\';
}

function hmRanking() {
  const sorted = Object.entries(hmData).sort((a,b) => {
    if (hmMetric === \\'yield\\') return b[1].yield - a[1].yield;
    if (hmMetric === \\'growth\\') return b[1].growth - a[1].growth;
    const r = {Low:0,Medium:1,High:2}; return r[a[1].risk]-r[b[1].risk];
  }).slice(0,8);
  const maxV = hmMetric === \\'risk\\' ? 3 : 8;
  document.getElementById(\\'hm-ranking-items\\').innerHTML = sorted.map(([name,d],i) => {
    const val = hmMetric === \\'yield\\' ? d.yield+\\'%\\' : hmMetric === \\'growth\\' ? \\'+\\'+d.growth+\\'%\\' : d.risk;
    const bw = hmMetric === \\'risk\\' ? (d.risk===\\'Low\\'?90:d.risk===\\'Medium\\'?55:20)
             : (parseFloat(hmMetric===\\'yield\\'?d.yield:d.growth)/maxV*100);
    const bc = hmColor(name, hmMetric);
    return \\'<div class="hm-rank-item" data-county="\\'+name+\\'" onclick="hmSelect(\\'+JSON.stringify(name)+\\')" style="display:flex;align-items:center;gap:0.7rem;padding:0.55rem 1.1rem;border-bottom:1px solid #2a2c30;cursor:pointer;transition:background 0.15s;"><span style="font-size:0.68rem;color:#4a4845;width:14px;">\\'+( i+1)+\\'</span><span style="font-size:0.82rem;font-weight:500;flex:1;color:white;">\\'+name+\\'</span><div style="width:45px;height:3px;background:#2a2c30;border-radius:2px;overflow:hidden;"><div style="width:\\'+bw+\\'%;height:100%;background:\\'+bc+\\';border-radius:2px;"></div></div><span style="font-size:0.82rem;font-weight:500;color:\\'+bc+\\';">\\'+val+\\'</span></div>\\';
  }).join(\\'\\');
}

hmColorMap(); hmRanking();
</script>
<!-- ── END HEATMAP SECTION ── -->
'''

# Find insertion point — after the deal checker section, before "Real Sample"
markers = [
    '<!-- ── END DEAL CHECKER SECTION ── -->',
    'Real Sample',
    'See exactly what you get',
    'real-sample',
]

inserted = False
for marker in markers:
    idx = content.find(marker)
    if idx != -1:
        insert_at = idx + len(marker)
        content = content[:insert_at] + '\n' + HEATMAP_SECTION + content[insert_at:]
        print(f"✅ Inserted heatmap after: '{marker[:50]}'")
        inserted = True
        break

if not inserted:
    print("❌ Could not find insertion point")
    print("Searching for nearby markers...")
    for m in ['section', 'Real Sample', 'deal-checker', 'snap']:
        idx = content.find(m)
        if idx != -1:
            print(f"  Found '{m}' at position {idx}")
else:
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("\nNow run:")
    print("  git add app.py")
    print("  git commit -m \"Add Ireland heatmap to homepage\"")
    print("  git push")
