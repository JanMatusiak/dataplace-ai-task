# dataplace-ai-task

Zadanie rekrutacyjne na stanowisko Data Scientist — dataplace.ai, 2026.

Celem analizy jest identyfikacja lokalizacji o najwyższym potencjale przychodowym dla nowych sklepów spożywczych klienta na obszarze Śląsk–Kraków. Pełne wyniki, wizualizacje i wnioski zawarte są w **`prezentacja.html`**.

---

## Struktura projektu

```
dataplace-ai-task/
├── notebooks/
│   ├── 01_exploratory_data_analysis.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model_and_interpretation.ipynb
│   └── 04_whitespot_analysis.ipynb
├── src/
│   ├── connectors.py
│   └── features.py
├── data/
│   ├── processed/
│   ├── outputs/
│   └── raw/
├── prezentacja.html
└── requirements.txt
```

---

## Notebooki

### `01_exploratory_data_analysis.ipynb`
Eksploracja wszystkich trzech źródeł danych: pliki CSV, AWS S3 i Snowflake.

- Analiza rozkładu `monthly_revenue` (target) — skośność, outliery IQR
- Analiza konkurencji (98 lokalizacji, 9 sieci, dominacja Żabki 61%)
- Analiza POI (335 punktów, 8 kategorii)
- Weryfikacja relacji `analysis_area` vs `ds_districts` — celowa rozbieżność, decyzja o użyciu wszystkich 50 lokalizacji do treningu
- Dane budynkowe S3 (955k rekordów) i demograficzne S3 (450k rekordów adresowych)
- Snowflake: filtrowanie do bbox + lipiec 2020 → 11.6M sygnałów, ~85k unikalnych użytkowników
- Analiza wzorców mobilności: rozkład sygnałów wg godziny i dnia tygodnia
- Wizualizacja folium z lokalizacjami, konkurencją i POI

Artefakty: `data/outputs/eda_map.html`, wizualizacje w .png

### `02_feature_engineering.ipynb`
Obliczenie 26 cech przestrzennych dla każdej z 50 lokalizacji w promieniu 1500m.

- Uzasadnienie wyboru promienia 1500m
- `compute_competitor_features` — liczba i odległość do konkurencji
- `compute_poi_features` — count + nearest_distance dla 8 kategorii POI
- `compute_buildings_features` — liczba budynków, residential_ratio (EPSG:2180)
- `compute_population_features` — populacja z danych adresowych S3
- `compute_footfall_features` — signals i unique_users z Snowflake (batch SQL, BATCH_SIZE=30)
- Iteracja 2: próba dodania `store_building_area` i `is_retail_building` 
- Iteracja 3: `signals_per_user` — marginalna poprawa R² nieistotna statystycznie przy n=50

Artefakty: `data/processed/features.csv`, `footfall_features.parquet`, GDFs jako parquet.

### `03_model_and_interpretation.ipynb`
Trening i ocena modeli predykcji revenue. Wybór modelu finalnego.

- Analiza korelacji Pearsona cech z targetem i między cechami (heatmapa)
- Testowanie 8 konfiguracji modeli: XGBoost (bazowy, tuned, zredukowany), Ridge, LASSO, SVR, XGBoost z rozszerzonymi cechami
- Ocena przez RepeatedKFold (5×10) — bardziej wiarygodna estymacja przy n=50
- Finalny model: XGBoost regularized, CV R²=0.175 ± 0.453, RMSE=83 599 PLN (poprawa 21% vs baseline)
- Analiza feature importance — zbieżność z korelacją Pearsona jako potwierdzenie wyników
- Uwagi o reprodukowalności: `n_jobs=1`, `OMP_NUM_THREADS=1`

Artefakty: `data/processed/model.joblib`, `feature_importance.csv`, `model_results.csv`, wizualizacje w .png

### `04_whitespot_analysis.ipynb`
Identyfikacja kandydatów na nowe lokalizacje w obszarze analizy.

- Generowanie siatki H3 (rozdzielczość 6, 162 komórki, ~1.2km średnica)
- Obliczenie 26 cech dla każdej komórki 
- Filtrowanie: min. 3000m od istniejącego sklepu klienta + 0 konkurentów w promieniu 1500m → 131 kandydatów
- Predykcja revenue i normalizacja do score 0–100
- Wizualizacja folium: heatmapa scoringu, top 10 kandydatów, istniejące sklepy
- Analiza top 3 lokalizacji z opisem kontekstu geograficznego
- SHAP waterfall plots dla top 3 — wyjaśnienie decyzji modelu per lokalizacja
- Porównanie top 3 kandydatów z top 3 istniejącymi sklepami (wg revenue)

Artefakty: `data/outputs/whitespot_map.html`, `data/processed/grid_features.csv`, wizualizacje w .png

---

## `src/`

### `connectors.py`
Funkcje do połączeń z zewnętrznymi źródłami danych:
- `get_snowflake_connection()` — połączenie z Snowflake (account: zy23245.west-europe.azure)
- `get_s3_client()` — klient boto3 dla AWS S3 (bucket: dataplace-recruitment, region: eu-central-1)

### `features.py`
Funkcje obliczające cechy przestrzenne dla zbioru lokalizacji. Używane zarówno w `02_feature_engineering.ipynb` (50 sklepów) jak i `04_whitespot_analysis.ipynb` (162 komórki H3):

- `compute_competitor_features(gdf, gdf_competitors, radius)` — competitor_count, nearest_competitor_m
- `compute_poi_features(gdf, gdf_poi, radius)` — count + nearest_distance dla 8 kategorii POI
- `compute_buildings_features(gdf, gdf_buildings, radius)` — building_count, residential_ratio
- `compute_population_features(gdf, gdf_population, radius)` — population (suma total)
- `compute_footfall_features(gdf, base_filter, radius)` — signals, unique_users (batch SQL, BATCH_SIZE=30)

Wszystkie obliczenia przestrzenne w promieniu wykonywane po reprojekcji do EPSG:2180 (Polska, metryczna). Footfall z Snowflake używa ST_DWITHIN z TO_GEOGRAPHY dla prawidłowych odległości geodezyjnych.

---

## Czas pracy

| Etap | Notebook / zadanie | Czas (h) |
|---|---|---|
| EDA | `01_exploratory_data_analysis.ipynb` | |
| Feature engineering | `02_feature_engineering.ipynb` | |
| Modelowanie | `03_model_and_interpretation.ipynb` | |
| Whitespot analysis | `04_whitespot_analysis.ipynb` | |
| Prezentacja | `prezentacja.html` | |
| Konfiguracja, setup, inne | — | |
| **Łącznie** | | |

---

## Wymagania

```
pip install -r requirements.txt
```

Dostępy do Snowflake i AWS S3 wymagane — dane konfiguracyjne w `.env` (nie wersjonowany).