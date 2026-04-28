# BRFSS Data Warehouse Project

Projekt rozszerza istniejący projekt ML o warstwę hurtowni danych pod raportowanie biznesowe.

## Co jest w projekcie

- `etl/build_warehouse.py` - pipeline ETL (CSV -> staging -> model gwiazdy -> data marts)
- `sql/create_schema.sql` - definicje tabel (staging + wymiary + tabela faktów)
- `sql/create_marts.sql` - widoki agregujące pod dashboard
- `dashboard/app.py` - dashboard Streamlit
- `data/brfss_dw.sqlite` - plik bazy tworzony po ETL

## Dlaczego hurtownia, skoro jest baza relacyjna

- Baza operacyjna przechowuje dane do przetwarzania i modelowania.
- Hurtownia ma strukturę pod analizę biznesową (model gwiazdy).
- Dzięki temu raporty agregujące są prostsze i szybsze (KPI, trendy, porównania segmentów).

## Model danych (gwiazda)

- Tabela faktów: `fact_health_survey`
- Wymiary:
  - `dim_year`
  - `dim_state`
  - `dim_age_group`
  - `dim_sex`
  - `dim_education`
  - `dim_income`
  - `dim_employment`
  - `dim_urban`

## Uruchomienie ETL

Z katalogu `dw_project`:

```powershell
python .\etl\build_warehouse.py
```

albo:

```powershell
.\run_etl.ps1
```

Po zakończeniu powstaje baza:

`dw_project/data/brfss_dw.sqlite`

## Uruchomienie dashboardu

Z katalogu `dw_project`:

```powershell
pip install -r .\requirements.txt
streamlit run .\dashboard\app.py
```

## Raporty agregujące (data marts)

- `vw_kpi_by_year` - KPI roczne: liczba respondentów, target count, target rate, średnie miary
- `vw_target_by_state` - target rate wg stanów i lat
- `vw_target_by_age_sex` - target rate wg wieku i płci

## Co pokazać na zaliczeniu

1. ETL: zasilenie hurtowni z pliku wejściowego.
2. Schemat: tabela faktów + wymiary (star schema).
3. SQL agregujący: widoki `vw_*`.
4. Dashboard: KPI + trendy + segmentacja.
5. Wniosek biznesowy: które grupy mają najwyższy target rate.
