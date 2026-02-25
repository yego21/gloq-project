import django
from datetime import date
from django.contrib.auth.models import User

# Change this to your username
user = User.objects.get(username='yego')

# 1. Birth profile + natal chart
from userprofile.models import BirthProfile
bp = BirthProfile.objects.get(user=user)
natal = bp.cached_chart_data

print("=== BIRTH PROFILE ===")
print(f"Birth date: {bp.birth_date}")
print(f"Birth timezone: {bp.birth_timezone}")
print(f"Has birth time: {bp.has_birth_time}")
print(f"Natal chart cached: {bool(natal)}")

if natal:
    print(f"Dominant element: {natal.get('dominant_element')}")
    print(f"Dominant modality: {natal.get('dominant_modality')}")
    print("Planets:")
    for p in natal.get('planets', []):
        print(f"  {p['name']:10} → {p['sign']:12} ({p.get('element', '?')})")

# 2. Today's snapshot — check reuse
from journal.models import DailyPlanetarySnapshot
snapshots_today = DailyPlanetarySnapshot.objects.filter(date=date.today())
print(f"\n=== DAILY SNAPSHOT ===")
print(f"Snapshots for today: {snapshots_today.count()} (should be 1)")

if snapshots_today.exists():
    snap = snapshots_today.first()
    print(f"Date: {snap.date} | Timezone: {snap.timezone}")
    positions = snap.planetary_data.get('planetary_positions', [])
    print("Current positions:")
    for p in positions:
        print(f"  {p['name']:10} → {p['sign']:12}")

# 3. Transits
from ...services.mystical.ai_chart_reading_svc import TransitCalculator
transit_calc = TransitCalculator(natal)
transits = transit_calc.calculate_transits(positions)

print(f"\n=== TRANSITS ({len(transits)} found) ===")
for t in transits[:10]:
    print(f"  {t['transit_planet']:10} {t['aspect_type']:12} natal {t['natal_planet']:10} | orb: {t.get('orb', '?')} | quality: {t.get('quality', '?')}")

# 4. What the tarot service would pick
from ...services.mystical.tarot_natal_svc import TarotNatalService
from ...services.mystical.tarot_deck import COSMIC_TAROT_DECK

svc = TarotNatalService(natal)
dominant_planet = svc.get_dominant_planetary_energy()
print(f"\n=== TAROT SERVICE ===")
print(f"Dominant planet: {dominant_planet}")

card = svc.select_card_by_transits(transits, COSMIC_TAROT_DECK)
print(f"Would select: {card['title']} ({card.get('element')}, planets: {card.get('planets')})")
print(f"Astro context: {svc.generate_astro_context(card, transits)}")
print(f"Natal insight: {svc.generate_natal_insight(card)}")