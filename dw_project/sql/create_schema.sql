DROP VIEW IF EXISTS vw_target_by_age_sex;
DROP VIEW IF EXISTS vw_target_by_state;
DROP VIEW IF EXISTS vw_kpi_by_year;

DROP TABLE IF EXISTS fact_health_survey;
DROP TABLE IF EXISTS dim_urban;
DROP TABLE IF EXISTS dim_employment;
DROP TABLE IF EXISTS dim_income;
DROP TABLE IF EXISTS dim_education;
DROP TABLE IF EXISTS dim_sex;
DROP TABLE IF EXISTS dim_age_group;
DROP TABLE IF EXISTS dim_state;
DROP TABLE IF EXISTS dim_year;
DROP TABLE IF EXISTS stg_brfss_model;

CREATE TABLE stg_brfss_model (
    respondent_id INTEGER,
    year_code INTEGER,
    state_code INTEGER,
    age_group_code INTEGER,
    sex_code INTEGER,
    education_code INTEGER,
    income_code INTEGER,
    employment_code INTEGER,
    urban_code INTEGER,
    checkup_code INTEGER,
    genhlth_code INTEGER,
    housing_code INTEGER,
    medcost_code INTEGER,
    persdoc_code INTEGER,
    target_flag INTEGER,
    bmi REAL,
    phys_hlth_days REAL,
    children_count REAL
);

CREATE TABLE dim_year (
    year_key INTEGER PRIMARY KEY,
    year_code INTEGER NOT NULL UNIQUE,
    year_label TEXT NOT NULL
);

CREATE TABLE dim_state (
    state_key INTEGER PRIMARY KEY,
    state_code INTEGER NOT NULL UNIQUE,
    state_label TEXT NOT NULL
);

CREATE TABLE dim_age_group (
    age_group_key INTEGER PRIMARY KEY,
    age_group_code INTEGER NOT NULL UNIQUE,
    age_group_label TEXT NOT NULL
);

CREATE TABLE dim_sex (
    sex_key INTEGER PRIMARY KEY,
    sex_code INTEGER NOT NULL UNIQUE,
    sex_label TEXT NOT NULL
);

CREATE TABLE dim_education (
    education_key INTEGER PRIMARY KEY,
    education_code INTEGER NOT NULL UNIQUE,
    education_label TEXT NOT NULL
);

CREATE TABLE dim_income (
    income_key INTEGER PRIMARY KEY,
    income_code INTEGER NOT NULL UNIQUE,
    income_label TEXT NOT NULL
);

CREATE TABLE dim_employment (
    employment_key INTEGER PRIMARY KEY,
    employment_code INTEGER NOT NULL UNIQUE,
    employment_label TEXT NOT NULL
);

CREATE TABLE dim_urban (
    urban_key INTEGER PRIMARY KEY,
    urban_code INTEGER NOT NULL UNIQUE,
    urban_label TEXT NOT NULL
);

CREATE TABLE fact_health_survey (
    fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    respondent_id INTEGER NOT NULL,
    year_key INTEGER NOT NULL,
    state_key INTEGER NOT NULL,
    age_group_key INTEGER NOT NULL,
    sex_key INTEGER NOT NULL,
    education_key INTEGER NOT NULL,
    income_key INTEGER NOT NULL,
    employment_key INTEGER NOT NULL,
    urban_key INTEGER NOT NULL,
    target_flag INTEGER NOT NULL,
    checkup_code INTEGER,
    genhlth_code INTEGER,
    housing_code INTEGER,
    medcost_code INTEGER,
    persdoc_code INTEGER,
    bmi REAL,
    phys_hlth_days REAL,
    children_count REAL,
    respondent_count INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (year_key) REFERENCES dim_year(year_key),
    FOREIGN KEY (state_key) REFERENCES dim_state(state_key),
    FOREIGN KEY (age_group_key) REFERENCES dim_age_group(age_group_key),
    FOREIGN KEY (sex_key) REFERENCES dim_sex(sex_key),
    FOREIGN KEY (education_key) REFERENCES dim_education(education_key),
    FOREIGN KEY (income_key) REFERENCES dim_income(income_key),
    FOREIGN KEY (employment_key) REFERENCES dim_employment(employment_key),
    FOREIGN KEY (urban_key) REFERENCES dim_urban(urban_key)
);

CREATE INDEX idx_fact_year ON fact_health_survey(year_key);
CREATE INDEX idx_fact_state ON fact_health_survey(state_key);
CREATE INDEX idx_fact_target ON fact_health_survey(target_flag);
