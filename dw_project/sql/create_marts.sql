CREATE VIEW vw_kpi_by_year AS
SELECT
    y.year_label AS year,
    SUM(f.respondent_count) AS respondents,
    SUM(f.target_flag) AS target_positive,
    ROUND(100.0 * SUM(f.target_flag) / NULLIF(SUM(f.respondent_count), 0), 2) AS target_rate_pct,
    ROUND(AVG(f.bmi), 2) AS avg_bmi,
    ROUND(AVG(f.phys_hlth_days), 2) AS avg_phys_hlth_days
FROM fact_health_survey f
JOIN dim_year y ON y.year_key = f.year_key
GROUP BY y.year_label
ORDER BY y.year_label;

CREATE VIEW vw_target_by_state AS
SELECT
    y.year_label AS year,
    s.state_label AS state_code,
    SUM(f.respondent_count) AS respondents,
    SUM(f.target_flag) AS target_positive,
    ROUND(100.0 * SUM(f.target_flag) / NULLIF(SUM(f.respondent_count), 0), 2) AS target_rate_pct
FROM fact_health_survey f
JOIN dim_year y ON y.year_key = f.year_key
JOIN dim_state s ON s.state_key = f.state_key
GROUP BY y.year_label, s.state_label;

CREATE VIEW vw_target_by_age_sex AS
SELECT
    y.year_label AS year,
    a.age_group_label AS age_group,
    sx.sex_label AS sex,
    SUM(f.respondent_count) AS respondents,
    SUM(f.target_flag) AS target_positive,
    ROUND(100.0 * SUM(f.target_flag) / NULLIF(SUM(f.respondent_count), 0), 2) AS target_rate_pct
FROM fact_health_survey f
JOIN dim_year y ON y.year_key = f.year_key
JOIN dim_age_group a ON a.age_group_key = f.age_group_key
JOIN dim_sex sx ON sx.sex_key = f.sex_key
GROUP BY y.year_label, a.age_group_label, sx.sex_label;
