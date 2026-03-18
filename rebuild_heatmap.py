"""
rebuild_heatmap.py
Completely replaces the heatmap section with a fixed version:
- Map fills its container properly
- No empty space below SVG
- Counties are larger and more visible
- Sidebar always beside map
Run from: C:\\Users\\WAFI\\irish-property-insights
"""
import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Remove entire existing heatmap section
pattern = r'<!-- ── HEATMAP SECTION ── -->.*?<!-- ── END HEATMAP SECTION ── -->'
match = re.search(pattern, content, re.DOTALL)
if match:
    print(f"Found existing heatmap section ({len(match.group())} chars), replacing...")
    content = content[:match.start()] + '%%HEATMAP%%' + content[match.end():]
else:
    print("No existing heatmap found, will insert after deal checker section")
    # Insert after deal checker section
    marker = '<!-- ── END DEAL CHECKER SECTION ── -->'
    idx = content.find(marker)
    if idx != -1:
        content = content[:idx+len(marker)] + '\n%%HEATMAP%%' + content[idx+len(marker):]
    else:
        print("ERROR: Cannot find insertion point")
        exit(1)

NEW_HEATMAP = '''<!-- ── HEATMAP SECTION ── -->
<section style="background:#0a0c0f;padding:3rem 1.5rem;border-top:1px solid #1a1c20;">
  <div style="max-width:1000px;margin:0 auto;">
    <div style="text-align:center;margin-bottom:2rem;">
      <div style="display:inline-block;font-size:0.7rem;font-weight:500;letter-spacing:0.18em;text-transform:uppercase;color:#c9a84c;border:1px solid #c9a84c;padding:0.3rem 0.8rem;border-radius:2px;margin-bottom:1rem;">Interactive Map</div>
      <h2 style="font-family:'Playfair Display',serif;font-size:clamp(1.5rem,3vw,2.2rem);font-weight:900;color:white;line-height:1.1;margin-bottom:0.6rem;">Irish Property Investment Heatmap</h2>
      <p style="color:#9a9690;font-size:0.9rem;font-weight:300;max-width:480px;margin:0 auto;">Click any county to see yield, growth and risk. Full micro-area rankings in the report.</p>
    </div>
    <div style="display:flex;gap:0.4rem;margin-bottom:1.5rem;justify-content:center;">
      <div style="display:flex;background:#1a1c20;border:1px solid #2a2c30;border-radius:3px;padding:0.25rem;">
        <button onclick="setMetric('yield',this)" class="hm-btn" style="padding:0.45rem 1rem;border:none;border-radius:2px;font-family:inherit;font-size:0.75rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;background:#c9a84c;color:#0f1014;transition:all 0.2s;">Rental Yield</button>
        <button onclick="setMetric('growth',this)" class="hm-btn" style="padding:0.45rem 1rem;border:none;border-radius:2px;font-family:inherit;font-size:0.75rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;background:transparent;color:#6b6860;transition:all 0.2s;">5yr Growth</button>
        <button onclick="setMetric('risk',this)" class="hm-btn" style="padding:0.45rem 1rem;border:none;border-radius:2px;font-family:inherit;font-size:0.75rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;background:transparent;color:#6b6860;transition:all 0.2s;">Risk Score</button>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 260px;gap:2rem;align-items:start;">
      <!-- MAP -->
      <div style="background:#111316;border:1px solid #1a1c20;border-radius:4px;padding:1rem;display:flex;align-items:center;justify-content:center;">
        <svg id="hm-svg" viewBox="20 12 265 310" xmlns="http://www.w3.org/2000/svg" style="width:100%;display:block;">
          <path id="hm-Donegal"   onclick="hmSel('Donegal')"   class="hmc" d="M90,22 L135,15 L165,30 L178,52 L158,68 L143,83 L120,76 L98,60 L83,45 Z"/>
          <path id="hm-Sligo"     onclick="hmSel('Sligo')"     class="hmc" d="M76,83 L106,76 L120,76 L128,91 L113,106 L90,106 L72,94 Z"/>
          <path id="hm-Leitrim"   onclick="hmSel('Leitrim')"   class="hmc" d="M120,76 L143,83 L147,98 L135,113 L120,109 L113,106 L128,91 Z"/>
          <path id="hm-Mayo"      onclick="hmSel('Mayo')"      class="hmc" d="M38,76 L75,68 L98,60 L98,83 L83,98 L72,94 L60,113 L38,121 L23,106 L30,91 Z"/>
          <path id="hm-Roscommon" onclick="hmSel('Roscommon')" class="hmc" d="M106,106 L128,98 L147,98 L151,117 L140,132 L120,132 L106,124 L102,113 Z"/>
          <path id="hm-Galway"    onclick="hmSel('Galway')"    class="hmc" d="M23,117 L60,113 L83,98 L98,106 L102,113 L106,124 L98,140 L83,158 L60,158 L38,155 L19,140 Z"/>
          <path id="hm-Clare"     onclick="hmSel('Clare')"     class="hmc" d="M60,158 L83,158 L98,140 L109,147 L113,163 L106,178 L86,186 L64,178 L57,166 Z"/>
          <path id="hm-Limerick"  onclick="hmSel('Limerick')"  class="hmc" d="M86,186 L106,178 L120,181 L132,196 L124,211 L106,215 L86,207 L79,196 Z"/>
          <path id="hm-Kerry"     onclick="hmSel('Kerry')"     class="hmc" d="M57,196 L79,196 L86,207 L83,226 L68,243 L49,245 L34,230 L38,211 Z"/>
          <path id="hm-Cork"      onclick="hmSel('Cork')"      class="hmc" d="M83,226 L106,215 L128,215 L147,222 L155,237 L147,252 L128,260 L106,260 L86,252 L72,243 L68,243 Z"/>
          <path id="hm-Tipperary" onclick="hmSel('Tipperary')" class="hmc" d="M109,147 L132,143 L151,151 L162,166 L158,184 L143,192 L132,196 L120,181 L113,163 Z"/>
          <path id="hm-Waterford" onclick="hmSel('Waterford')" class="hmc" d="M128,215 L147,222 L166,215 L173,203 L162,192 L158,184 L143,192 L132,196 Z"/>
          <path id="hm-Wexford"   onclick="hmSel('Wexford')"   class="hmc" d="M166,215 L185,207 L200,215 L204,230 L192,245 L173,249 L155,237 L147,222 Z"/>
          <path id="hm-Kilkenny"  onclick="hmSel('Kilkenny')"  class="hmc" d="M151,151 L170,151 L185,162 L185,181 L173,192 L162,192 L158,184 L162,166 Z"/>
          <path id="hm-Carlow"    onclick="hmSel('Carlow')"    class="hmc" d="M170,151 L189,147 L200,158 L196,173 L185,181 L185,162 Z"/>
          <path id="hm-Laois"     onclick="hmSel('Laois')"     class="hmc" d="M151,117 L173,121 L192,128 L200,143 L189,147 L170,151 L151,151 L140,132 Z"/>
          <path id="hm-Offaly"    onclick="hmSel('Offaly')"    class="hmc" d="M128,106 L151,105 L173,106 L177,121 L173,121 L151,117 L140,124 L128,117 Z"/>
          <path id="hm-Westmeath" onclick="hmSel('Westmeath')" class="hmc" d="M140,85 L166,84 L188,91 L192,106 L177,106 L173,106 L151,105 L140,98 Z"/>
          <path id="hm-Longford"  onclick="hmSel('Longford')"  class="hmc" d="M128,76 L151,74 L166,84 L155,94 L140,98 L140,85 L132,79 Z"/>
          <path id="hm-Cavan"     onclick="hmSel('Cavan')"     class="hmc" d="M147,60 L173,57 L192,64 L196,79 L188,91 L166,84 L151,74 L143,66 Z"/>
          <path id="hm-Monaghan"  onclick="hmSel('Monaghan')"  class="hmc" d="M173,49 L200,45 L215,57 L211,72 L192,75 L192,64 L181,55 Z"/>
          <path id="hm-Meath"     onclick="hmSel('Meath')"     class="hmc" d="M188,91 L215,87 L230,98 L230,117 L211,124 L196,121 L192,106 Z"/>
          <path id="hm-Louth"     onclick="hmSel('Louth')"     class="hmc" d="M211,72 L234,68 L243,83 L234,98 L215,98 L215,87 Z"/>
          <path id="hm-Dublin"    onclick="hmSel('Dublin')"    class="hmc" d="M230,98 L251,94 L260,109 L252,124 L234,128 L230,117 Z"/>
          <path id="hm-Wicklow"   onclick="hmSel('Wicklow')"   class="hmc" d="M234,128 L252,124 L268,136 L264,155 L249,166 L230,162 L222,147 L226,134 Z"/>
          <path id="hm-Kildare"   onclick="hmSel('Kildare')"   class="hmc" d="M196,121 L218,117 L230,128 L226,143 L211,147 L200,143 L192,128 Z"/>
          <!-- NI greyed -->
          <path style="fill:#1a1c20;stroke:#111316;stroke-width:1;pointer-events:none;" d="M165,30 L218,23 L232,45 L218,68 L188,76 L158,68 L178,52 Z"/>
          <!-- Labels -->
          <text x="118" y="50"  font-size="7.5" fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Donegal</text>
          <text x="98"  y="93"  font-size="6.5" fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Sligo</text>
          <text x="133" y="97"  font-size="5.5" fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Leitrim</text>
          <text x="62"  y="100" font-size="7"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Mayo</text>
          <text x="127" y="117" font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Roscommon</text>
          <text x="64"  y="134" font-size="7"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Galway</text>
          <text x="86"  y="167" font-size="6.5" fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Clare</text>
          <text x="106" y="199" font-size="6.5" fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Limerick</text>
          <text x="59"  y="220" font-size="6.5" fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Kerry</text>
          <text x="113" y="238" font-size="7"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Cork</text>
          <text x="136" y="170" font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Tipperary</text>
          <text x="150" y="205" font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Waterford</text>
          <text x="178" y="228" font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Wexford</text>
          <text x="170" y="171" font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Kilkenny</text>
          <text x="184" y="158" font-size="5.5" fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Carlow</text>
          <text x="170" y="137" font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Laois</text>
          <text x="152" y="112" font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Offaly</text>
          <text x="163" y="96"  font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Westmeath</text>
          <text x="147" y="83"  font-size="5.5" fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Longford</text>
          <text x="170" y="72"  font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Cavan</text>
          <text x="194" y="61"  font-size="5.5" fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Monaghan</text>
          <text x="210" y="107" font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Meath</text>
          <text x="224" y="84"  font-size="5.5" fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Louth</text>
          <text x="243" y="111" font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Dublin</text>
          <text x="249" y="147" font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Wicklow</text>
          <text x="212" y="133" font-size="6"   fill="rgba(255,255,255,0.55)" text-anchor="middle" pointer-events="none">Kildare</text>
        </svg>
      </div>
      <!-- SIDEBAR -->
      <div>
        <div id="hm-info" style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;padding:1.5rem 1.2rem;text-align:center;color:#4a4845;font-size:0.82rem;line-height:1.6;margin-bottom:1rem;">
          <div style="font-size:1.3rem;margin-bottom:0.6rem;">🗺️</div>
          Click any county on the map
        </div>
        <div style="margin-bottom:1rem;">
          <div style="font-size:0.65rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.4rem;" id="hm-leg-title">Rental Yield</div>
          <div style="height:6px;border-radius:2px;background:linear-gradient(to right,#0d3d22,#1a6b3c,#c9a84c,#d4821a,#c0392b);margin-bottom:0.3rem;"></div>
          <div style="display:flex;justify-content:space-between;font-size:0.65rem;color:#4a4845;"><span id="hm-leg-lo">Low (3%)</span><span id="hm-leg-hi">High (8%+)</span></div>
        </div>
        <div style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;overflow:hidden;">
          <div style="padding:0.6rem 1rem;font-size:0.65rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;border-bottom:1px solid #2a2c30;" id="hm-rank-title">Top Counties by Yield</div>
          <div id="hm-rank-list"></div>
        </div>
      </div>
    </div>
  </div>
</section>
<style>
.hmc { stroke:#111316; stroke-width:1.2; cursor:pointer; transition:filter 0.12s, stroke 0.12s; }
.hmc:hover { filter:brightness(1.3); stroke:white; stroke-width:2; }
.hmc.hm-sel { stroke:white; stroke-width:2.5; filter:brightness(1.35); }
.hm-btn { transition: background 0.2s, color 0.2s; }
@media(max-width:680px){
  div[style*="grid-template-columns:1fr 260px"] { display:flex !important; flex-direction:column !important; }
}
</style>
<script>
const hmD={Dublin:{yield:5.5,growth:5.3,risk:'Medium',signal:'STRONG BUY',price:484581},Cork:{yield:5.1,growth:6.2,risk:'Low',signal:'STRONG BUY',price:320000},Galway:{yield:4.8,growth:5.8,risk:'Low',signal:'STRONG BUY',price:285000},Kildare:{yield:4.2,growth:6.8,risk:'Low',signal:'STRONG BUY',price:355000},Meath:{yield:4.5,growth:7.1,risk:'Low',signal:'STRONG BUY',price:320000},Wicklow:{yield:3.9,growth:5.5,risk:'Low',signal:'MODERATE',price:380000},Limerick:{yield:5.4,growth:6.9,risk:'Low',signal:'STRONG BUY',price:245000},Waterford:{yield:5.2,growth:5.1,risk:'Medium',signal:'STRONG BUY',price:220000},Louth:{yield:5.0,growth:7.1,risk:'Low',signal:'STRONG BUY',price:235000},Wexford:{yield:4.6,growth:6.3,risk:'Low',signal:'STRONG BUY',price:210000},Kilkenny:{yield:4.4,growth:5.8,risk:'Low',signal:'MODERATE',price:230000},Tipperary:{yield:5.8,growth:4.2,risk:'Medium',signal:'MODERATE',price:175000},Clare:{yield:5.3,growth:5.6,risk:'Low',signal:'STRONG BUY',price:195000},Kerry:{yield:4.9,growth:6.1,risk:'Medium',signal:'STRONG BUY',price:215000},Mayo:{yield:6.2,growth:3.8,risk:'Medium',signal:'MODERATE',price:145000},Sligo:{yield:5.9,growth:4.1,risk:'Medium',signal:'MODERATE',price:155000},Donegal:{yield:6.5,growth:3.5,risk:'High',signal:'MODERATE',price:125000},Roscommon:{yield:6.8,growth:3.2,risk:'High',signal:'AVOID',price:115000},Laois:{yield:5.1,growth:5.9,risk:'Low',signal:'STRONG BUY',price:185000},Offaly:{yield:5.3,growth:5.2,risk:'Medium',signal:'MODERATE',price:165000},Westmeath:{yield:5.0,growth:5.4,risk:'Low',signal:'STRONG BUY',price:175000},Longford:{yield:7.1,growth:2.8,risk:'High',signal:'AVOID',price:95000},Cavan:{yield:6.1,growth:3.6,risk:'High',signal:'AVOID',price:130000},Monaghan:{yield:5.7,growth:4.0,risk:'Medium',signal:'MODERATE',price:140000},Carlow:{yield:5.2,growth:6.1,risk:'Low',signal:'STRONG BUY',price:190000},Leitrim:{yield:7.8,growth:2.5,risk:'High',signal:'AVOID',price:85000}};
let hmM='yield',hmS=null;
function hmClr(n,m){const d=hmD[n];if(!d)return'#1a1c20';if(m==='yield'){const v=d.yield;if(v>=7)return'#c0392b';if(v>=6)return'#d4821a';if(v>=5.5)return'#b8962e';if(v>=5)return'#2d8a5e';if(v>=4)return'#1a6b3c';return'#0d3d22';}if(m==='growth'){const v=d.growth;if(v>=7)return'#1a6b3c';if(v>=6)return'#2d8a5e';if(v>=5)return'#b8962e';if(v>=4)return'#d4821a';return'#c0392b';}if(d.risk==='Low')return'#1a6b3c';if(d.risk==='Medium')return'#b8962e';return'#c0392b';}
function hmPaint(){Object.keys(hmD).forEach(n=>{const e=document.getElementById('hm-'+n);if(e)e.style.fill=hmClr(n,hmM);});}
function setMetric(m,btn){hmM=m;document.querySelectorAll('.hm-btn').forEach(b=>{b.style.background='transparent';b.style.color='#6b6860';});btn.style.background='#c9a84c';btn.style.color='#0f1014';const lt={yield:'Rental Yield',growth:'5yr Growth',risk:'Risk Score'};const lo={yield:'Low (3%)',growth:'Low (2%)',risk:'Low Risk'};const hi={yield:'High (8%+)',growth:'High (7%+)',risk:'High Risk'};document.getElementById('hm-leg-title').textContent=lt[m];document.getElementById('hm-leg-lo').textContent=lo[m];document.getElementById('hm-leg-hi').textContent=hi[m];document.getElementById('hm-rank-title').textContent=m==='yield'?'Top Counties by Yield':m==='growth'?'Top Counties by Growth':'Lowest Risk Counties';hmPaint();hmRank();if(hmS)hmCard(hmS);}
function hmSel(n){document.querySelectorAll('.hmc').forEach(e=>e.classList.remove('hm-sel'));const el=document.getElementById('hm-'+n);if(el)el.classList.add('hm-sel');hmS=n;hmCard(n);document.querySelectorAll('.hm-ri').forEach(i=>i.style.background=i.dataset.c===n?'#22252a':'transparent');}
function hmCard(n){const d=hmD[n];if(!d)return;const sc=d.signal==='STRONG BUY'?'background:rgba(26,107,60,0.3);color:#4ade80':d.signal==='MODERATE'?'background:rgba(201,168,76,0.2);color:#c9a84c':'background:rgba(192,57,43,0.2);color:#ef4444';const gc=d.growth>=6?'#4ade80':d.growth>=4?'#c9a84c':'#ef4444';const yc=d.yield>=5?'#4ade80':d.yield>=4?'#c9a84c':'#ef4444';const rc=d.risk==='Low'?'#4ade80':d.risk==='Medium'?'#c9a84c':'#ef4444';const has=['Dublin','Cork','Galway','Kildare','Kerry','Meath','Wicklow'].includes(n);const cta=has?`<a href="/#reports" style="display:block;text-align:center;padding:0.65rem;background:#c9a84c;color:#0f1014;border-radius:3px;font-size:0.72rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;text-decoration:none;margin-top:0.8rem;">Unlock All Micro-Areas in ${n} — €29 →</a>`:`<a href="/#snap" style="display:block;text-align:center;padding:0.65rem;background:#1a1c20;color:#9a9690;border:1px solid #2a2c30;border-radius:3px;font-size:0.72rem;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;text-decoration:none;margin-top:0.8rem;">Get Free ${n} Snapshot →</a>`;document.getElementById('hm-info').innerHTML=`<div style="padding:0.9rem 1rem 0.7rem;border-bottom:1px solid #2a2c30;"><div style="font-family:'Playfair Display',serif;font-size:1.2rem;font-weight:700;color:white;">${n}</div><div style="display:inline-block;font-size:0.6rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;padding:0.2rem 0.5rem;border-radius:2px;margin-top:0.3rem;${sc};">${d.signal}</div></div><div style="display:grid;grid-template-columns:1fr 1fr;"><div style="padding:0.7rem 1rem;border-right:1px solid #2a2c30;border-bottom:1px solid #2a2c30;"><div style="font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.2rem;">Gross Yield</div><div style="font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:700;color:${yc};">${d.yield}%</div></div><div style="padding:0.7rem 1rem;border-bottom:1px solid #2a2c30;"><div style="font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.2rem;">5yr Growth</div><div style="font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:700;color:${gc};">+${d.growth}%</div></div><div style="padding:0.7rem 1rem;border-right:1px solid #2a2c30;"><div style="font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.2rem;">Risk</div><div style="font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:700;color:${rc};">${d.risk}</div></div><div style="padding:0.7rem 1rem;"><div style="font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.2rem;">Median Price</div><div style="font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:700;color:white;">€${d.price.toLocaleString()}</div></div></div>${cta}`;}
function hmRank(){const sorted=Object.entries(hmD).sort((a,b)=>{if(hmM==='yield')return b[1].yield-a[1].yield;if(hmM==='growth')return b[1].growth-a[1].growth;const r={Low:0,Medium:1,High:2};return r[a[1].risk]-r[b[1].risk];}).slice(0,8);document.getElementById('hm-rank-list').innerHTML=sorted.map(([n,d],i)=>{const val=hmM==='yield'?d.yield+'%':hmM==='growth'?'+'+d.growth+'%':d.risk;const bw=hmM==='risk'?(d.risk==='Low'?90:d.risk==='Medium'?55:20):(parseFloat(hmM==='yield'?d.yield:d.growth)/8*100);const bc=hmClr(n,hmM);return`<div class="hm-ri" data-c="${n}" onclick="hmSel('${n}')" style="display:flex;align-items:center;gap:0.6rem;padding:0.5rem 1rem;border-bottom:1px solid #2a2c30;cursor:pointer;transition:background 0.12s;"><span style="font-size:0.65rem;color:#4a4845;width:12px;">${i+1}</span><span style="font-size:0.8rem;font-weight:500;flex:1;color:white;">${n}</span><div style="width:40px;height:3px;background:#2a2c30;border-radius:2px;overflow:hidden;"><div style="width:${bw}%;height:100%;background:${bc};border-radius:2px;"></div></div><span style="font-size:0.8rem;font-weight:600;color:${bc};">${val}</span></div>`;}).join('');}
hmPaint();hmRank();
</script>
<!-- ── END HEATMAP SECTION ── -->'''

content = content.replace('%%HEATMAP%%', NEW_HEATMAP)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Heatmap section completely rebuilt!")
print("\nNow run:")
print("  git add app.py")
print("  git commit -m \"Rebuild heatmap - fix size and layout\"")
print("  git push")
