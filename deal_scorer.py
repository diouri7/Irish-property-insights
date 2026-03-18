import pandas as pd
import numpy as np
import joblib
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder

print('Libraries loaded ✅')

# ── LOAD DATA ──
PPR_PATH = 'PPR-ALL.csv'
df = pd.read_csv(PPR_PATH, encoding='latin-1', low_memory=False)
print('Raw shape:', df.shape)
print('Columns:', df.columns.tolist())

# ── RENAME COLUMNS ──
df.columns = [
    'date_of_sale', 'address', 'county', 'eircode',
    'price', 'not_full_market_price', 'vat_exclusive',
    'description', 'property_size_desc'
]

# ── CLEAN PRICE ──
df['price'] = df['price'].astype(str).str.replace(r'[^\d.]', '', regex=True)
df['price'] = pd.to_numeric(df['price'], errors='coerce')

# ── PARSE DATE ──
df['date_of_sale'] = pd.to_datetime(df['date_of_sale'], dayfirst=True, errors='coerce')
df['year'] = df['date_of_sale'].dt.year

# ── MICRO AREA ──
df['micro_area'] = df['address'].astype(str).apply(
    lambda x: x.split(',')[0].strip().title()
)

# ── CLEAN COUNTY ──
df['county'] = df['county'].astype(str).str.strip().str.title()

# ── FILTER ──
df = df[
    (df['price'] >= 30_000) &
    (df['price'] <= 5_000_000) &
    (df['year'] >= 2010) &
    (df['not_full_market_price'].astype(str).str.strip() == 'No')
].copy()

print('Cleaned shape:', df.shape)

if len(df) == 0:
    print('ERROR: No rows after filtering!')
    print('not_full_market_price unique values:', df['not_full_market_price'].unique())
    exit()

# ── ENCODE ──
le_county = LabelEncoder()
le_desc = LabelEncoder()
le_micro = LabelEncoder()

df['county_enc'] = le_county.fit_transform(df['county'].fillna('Unknown'))
df['desc_enc'] = le_desc.fit_transform(df['description'].fillna('Unknown'))
df['micro_enc'] = le_micro.fit_transform(df['micro_area'].fillna('Unknown'))
df['log_price'] = np.log1p(df['price'])

FEATURES = ['county_enc', 'micro_enc', 'desc_enc', 'year']
TARGET = 'log_price'

model_df = df[FEATURES + [TARGET]].dropna()
print('Model dataset shape:', model_df.shape)

# ── TRAIN ──
X = model_df[FEATURES]
y = model_df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestRegressor(
    n_estimators=200,
    max_depth=15,
    min_samples_leaf=5,
    n_jobs=-1,
    random_state=42
)

print('Training model... (this takes 1-2 minutes)')
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
mae = mean_absolute_error(np.expm1(y_test), np.expm1(y_pred))
r2 = r2_score(y_test, y_pred)

print(f'✅ Model trained')
print(f'   MAE:  €{mae:,.0f}')
print(f'   R²:   {r2:.3f}')

# ── SAVE ──
joblib.dump(model, 'deal_scorer_model.pkl')
joblib.dump(le_county, 'le_county.pkl')
joblib.dump(le_desc, 'le_desc.pkl')
joblib.dump(le_micro, 'le_micro.pkl')

known = {
    'counties': sorted(le_county.classes_.tolist()),
    'descriptions': sorted(le_desc.classes_.tolist()),
}
with open('known_values.json', 'w') as f:
    json.dump(known, f)

print('✅ Model and encoders saved!')

# ── TEST ──
def score_deal(county, area, asking_price, year=2024):
    county_title = county.strip().title()
    area_title = area.strip().title()

    if county_title not in le_county.classes_:
        return {'error': f'County "{county}" not found'}

    if area_title not in le_micro.classes_:
        county_areas = df[df['county'] == county_title]['micro_area'].value_counts()
        area_title = county_areas.index[0] if len(county_areas) > 0 else le_micro.classes_[0]
        fallback = True
    else:
        fallback = False

    desc_default = le_desc.classes_[0]

    county_enc = le_county.transform([county_title])[0]
    micro_enc = le_micro.transform([area_title])[0]
    desc_enc = le_desc.transform([desc_default])[0]

    X_input = pd.DataFrame([{
        'county_enc': county_enc,
        'micro_enc': micro_enc,
        'desc_enc': desc_enc,
        'year': year
    }])

    log_pred = model.predict(X_input)[0]
    predicted_price = np.expm1(log_pred)
    diff_pct = ((asking_price - predicted_price) / predicted_price) * 100

    if diff_pct <= -15:   verdict = '🟢 STRONG BUY'
    elif diff_pct <= -5:  verdict = '🟢 GOOD DEAL'
    elif diff_pct <= 5:   verdict = '🟡 FAIR'
    elif diff_pct <= 15:  verdict = '🟠 OVERPRICED'
    else:                 verdict = '🔴 AVOID'

    return {
        'verdict': verdict,
        'asking_price': f'€{asking_price:,.0f}',
        'predicted_market_value': f'€{predicted_price:,.0f}',
        'difference': f'{diff_pct:+.1f}%',
        'fallback_used': fallback
    }

print('\n── TEST RESULTS ──')
test_cases = [
    ('Dublin', 'Ballymun', 320_000),
    ('Dublin', 'Blackrock', 750_000),
    ('Cork', 'Douglas', 420_000),
    ('Galway', 'Salthill', 380_000),
]

for county, area, price in test_cases:
    result = score_deal(county, area, price)
    print(f'\n📍 {area}, {county} — Asking €{price:,}')
    for k, v in result.items():
        print(f'   {k}: {v}')
