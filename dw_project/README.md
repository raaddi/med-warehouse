# Med Warehouse: warehouse and dashboard

This directory contains the ETL pipeline, SQL definitions and Streamlit application.

See the repository documentation for the project overview, data model, metric definitions, limitations and complete setup instructions:

- [English documentation](../README.md)
- [Dokumentacja po polsku](../README.pl.md)

After preparing the input CSV as described there, you can run the following from this directory:

```bash
python etl/build_warehouse.py
python -m streamlit run dashboard/app.py
```

The generated database is `data/brfss_dw.sqlite`, relative to this directory. Each ETL run rebuilds the warehouse tables and views.
