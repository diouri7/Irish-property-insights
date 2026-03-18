"""
Three quick wins - FIXED VERSION:
  1. Sticky CTA bar (landing page only)
  2. Fix vague sample area names
  3. Countdown timer on pricing

Run: python quick_wins.py
"""
import ast

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# ── 1. FIX SAMPLE NAMES ──
NAME_FIXES = [
    ('<span class="rp-area">Clondalkin</span>',        '<span class="rp-area">Clondalkin, Dublin 22</span>'),
    ('<span class="rp-area">Main St</span>',           '<span class="rp-area">Main St, Blanchardstown</span>'),
    ('<span class="rp-area">Northwood</span>',         '<span class="rp-area">Northwood, Santry D9</span>'),
    ('<td>3</td><td>Clondalkin</td>',                  '<td>3</td><td>Clondalkin, Dublin 22</td>'),
    ('<td>4</td><td>Main St</td>',                     '<td>4</td><td>Main St, Blanchardstown</td>'),
    ('<tr class="blur-row"><td>5</td><td>Northwood</td>', '<tr class="blur-row"><td>5</td><td>Northwood, Santry D9</td>'),
    ('<td>Swords, Dublin</td>',        '<td>Swords, Dublin 17</td>'),
    ('<td>Salthill, Galway</td>',      '<td>Salthill, Co. Galway</td>'),
    ('<td>Castletroy, Limerick</td>',  '<td>Castletroy, Co. Limerick</td>'),
]
for old, new in NAME_FIXES:
    if old in content:
        content = content.replace(old, new)
        changes += 1
        print(f"  + Fixed name: {old[20:50]}")
    else:
        print(f"  - Not found: {old[20:50]}")

# ── 2. COUNTDOWN TIMER ──
OLD_URG = '<p style="font-size:.82rem;color:var(--gold);margin-top:.5rem;font-weight:600">\U0001f680 Founding price \u2014 \u20ac49 after launch. Lock in \u20ac29 now.</p>'
NEW_URG = '<p style="font-size:.82rem;color:var(--gold);margin-top:.5rem;font-weight:600">\U0001f680 Founding price \u2014 locks in <span id="cdTimer">calculating...</span></p><script>(function(){var d=new Date("2026-04-01T23:59:59");function p(n){return n<10?"0"+n:n;}function u(){var n=new Date(),diff=d-n;if(diff<=0){document.getElementById("cdTimer").textContent="soon";return;}var dy=Math.floor(diff/86400000),h=Math.floor((diff%86400000)/3600000),m=Math.floor((diff%3600000)/60000),s=Math.floor((diff%60000)/1000);document.getElementById("cdTimer").textContent="in "+dy+"d "+p(h)+"h "+p(m)+"m "+p(s)+"s";}u();setInterval(u,1000);})();</script>'

if OLD_URG in content:
    content = content.replace(OLD_URG, NEW_URG)
    changes += 1
    print("  + Added countdown timer")
else:
    print("  - Urgency text not found")

# ── 3. STICKY CTA BAR (LANDING PAGE ONLY) ──
STICKY_CSS = """
#stickyCTA{position:fixed;bottom:0;left:0;right:0;z-index:200;background:rgba(11,17,32,.95);backdrop-filter:blur(12px);border-top:1px solid rgba(16,185,129,.25);padding:.75rem 2rem;display:flex;align-items:center;justify-content:space-between;gap:1rem;transform:translateY(100%);transition:transform .35s ease;flex-wrap:wrap;}
#stickyCTA.visible{transform:translateY(0);}
#stickyCTA .sc-msg{font-size:.88rem;color:var(--t2);flex:1;min-width:180px;}
#stickyCTA .sc-msg strong{color:var(--t1);}
#stickyCTA .sc-actions{display:flex;gap:.6rem;align-items:center;flex-shrink:0;}
#stickyCTA .sc-dismiss{background:none;border:none;color:var(--t3);cursor:pointer;font-size:1.2rem;padding:.2rem .5rem;line-height:1;}
@media(max-width:480px){#stickyCTA{padding:.6rem 1rem;}#stickyCTA .sc-msg{font-size:.8rem;}}
"""

STICKY_HTML = """<!-- STICKY BAR -->
<div id="stickyCTA">
  <p class="sc-msg"><strong>IrishPropertyInsights</strong> &mdash; free micro-area data for every Irish county</p>
  <div class="sc-actions">
    <a href="#snap" class="bp" style="padding:.6rem 1.2rem;font-size:.85rem;">Free Snapshot &rarr;</a>
    <a href="#reports" class="bs" style="padding:.6rem 1.2rem;font-size:.85rem;">Full Report &euro;29</a>
    <button class="sc-dismiss" onclick="var e=document.getElementById(&quot;stickyCTA&quot;);e.style.display=&quot;none&quot;;" title="Dismiss">&times;</button>
  </div>
</div>
<script>(function(){var b=document.getElementById("stickyCTA");window.addEventListener("scroll",function(){b.style.display!=="none"&&(window.scrollY>500?b.classList.add("visible"):b.classList.remove("visible"));},{passive:true});})();</script>
"""

if 'stickyCTA' not in content:
    # Insert CSS: find last </style> before first <body> in LANDING_HTML
    landing_start = content.find('LANDING_HTML = """')
    body_pos = content.find('<body>', landing_start)
    style_pos = content.rfind('</style>', landing_start, body_pos)
    if style_pos != -1:
        content = content[:style_pos] + STICKY_CSS + content[style_pos:]
        changes += 1
        print("  + Added sticky CTA CSS")
    else:
        print("  - CSS insertion point not found")

    # Insert HTML: after the landing page <body> tag (unique nav anchor)
    ANCHOR = '<body>\n<nav><a href="#" class="nl">Irish<span>Property</span>Insights</a>'
    if ANCHOR in content:
        content = content.replace(ANCHOR,
            '<body>\n' + STICKY_HTML + '<nav><a href="#" class="nl">Irish<span>Property</span>Insights</a>', 1)
        changes += 1
        print("  + Added sticky CTA HTML (landing page only)")
    else:
        print("  - Nav anchor not found for sticky HTML")
else:
    print("  - Sticky CTA already present")

# ── SYNTAX CHECK ──
try:
    ast.parse(content)
    print("  + Syntax OK")
except SyntaxError as e:
    print(f"  X SYNTAX ERROR line {e.lineno}: {e.msg}")
    print("  File NOT written.")
    exit(1)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print(f"\nDone - {changes} changes applied.")
print("git add app.py && git commit -m 'Sticky CTA, countdown, fix names' && git push")
