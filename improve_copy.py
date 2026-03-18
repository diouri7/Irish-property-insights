"""
improve_copy.py
Improves CTAs and copy throughout the homepage
Run from: C:\\Users\\WAFI\\irish-property-insights
"""

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = [
    # Hero headline - more specific and punchy
    (
        'Find the best property investment areas in Ireland — using real data.',
        'Stop Guessing. Start Investing With Data.'
    ),
    # Hero subheadline
    (
        'Most investors guess. We rank every micro-area across all 26 counties by rental yield, 5-year growth, and investment risk — built on 15 years of Property Price Register data and official RTB rental figures.',
        'We rank every micro-area across all 26 counties by rental yield, 5-year price growth, and investment risk — built on 727,000 real transactions from the Property Price Register and official RTB rental data.'
    ),
    # Primary CTA
    (
        'Get Free County Snapshot →',
        'See Top Investment Areas Free →'
    ),
    # Secondary CTA
    (
        'View Full Reports — €29',
        'Unlock Full County Report — €29'
    ),
    # Below hero CTAs
    (
        'Free snapshot available for every county — no credit card needed',
        'Free for every county — no credit card, no signup required'
    ),
    # "See exactly what you get" section header
    (
        'See exactly what you get',
        'Real data. Real areas. Real signals.'
    ),
    # Three questions section header
    (
        'Three questions every investor needs answered',
        'Three questions every Irish property investor needs answered'
    ),
    # "Get Free Snapshot" mid-page CTA
    (
        '>Get Free Snapshot →<',
        '>See Top Areas For Free →<'
    ),
    # Snapshot section header
    (
        'Get your free county snapshot',
        'Get your free investor snapshot'
    ),
    # Snapshot section subheading
    (
        'A 2-page investment briefing for any Irish county. See exactly what the full report covers — before you buy.',
        'A 2-page investment briefing for any Irish county — free, instant, no credit card. See the top areas before you commit to the full report.'
    ),
    # Full report section header
    (
        'Get the full investment report',
        'Unlock the full county report'
    ),
    # Full report subheading
    (
        'Comprehensive micro-area analysis for any of Ireland\'s 26 counties. Every area scored and ranked.',
        'Every micro-area in your chosen county — ranked by yield, growth, and risk. Built for investors who want data, not guesswork.'
    ),
    # Buy button
    (
        'Get Full Report — €29 →',
        'Get Instant Access — €29 →'
    ),
    # Footer founding price note
    (
        '🚀 Founding price — will increase as we add features',
        '🚀 Founding price — €49 after launch. Lock in €29 now.'
    ),
    # "Who it\'s for" - straight talk header
    (
        'Is this report right for you?',
        'This report is built for serious investors'
    ),
    # Straight talk subhead
    (
        "We'd rather be honest upfront than waste your time.",
        "We built this for people who make decisions based on data, not headlines."
    ),
    # How it works header
    (
        'From raw data to investment insight',
        'How we turn 15 years of raw data into clear investment signals'
    ),
    # Step 4
    (
        'Delivered as a detailed PDF report',
        'Delivered instantly as a detailed PDF report'
    ),
    # Micro-area intelligence callout
    (
        'Micro-area intelligence, not county averages',
        'Micro-area precision — not vague county averages'
    ),
]

count = 0
for old, new in changes:
    if old in content:
        content = content.replace(old, new)
        print(f"✓ Updated: {old[:60]}...")
        count += 1
    else:
        print(f"✗ Not found: {old[:60]}...")

print(f"\n{count}/{len(changes)} changes applied")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\nNow run:")
print("  git add app.py")
print("  git commit -m \"Improve CTAs and copy\"")
print("  git push")
