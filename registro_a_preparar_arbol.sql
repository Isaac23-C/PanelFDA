USE covid_19pruebas;

DROP TABLE IF EXISTS registro_a_pacientes_arbol;

CREATE TABLE registro_a_pacientes_arbol (
    nuevos VARCHAR(255) NOT NULL,
    diagnostico VARCHAR(255) NOT NULL,
    unidad_medica VARCHAR(255) NOT NULL,
    mortalidad TINYINT(1) NOT NULL,
    total_registros_intervencion INT NOT NULL,
    total_intervenciones_distintas INT NOT NULL,
    total_cantidad INT NOT NULL,
    total_tarifa BIGINT NOT NULL,
    interv_urgencias_covid TINYINT(1) NOT NULL,
    interv_hospitalizacion_dia_cama TINYINT(1) NOT NULL,
    interv_prueba_pcr TINYINT(1) NOT NULL,
    interv_biometria_hematica TINYINT(1) NOT NULL,
    interv_quimica_sanguinea TINYINT(1) NOT NULL,
    interv_dimero_d TINYINT(1) NOT NULL,
    interv_gasometria TINYINT(1) NOT NULL,
    interv_radiografia_torax TINYINT(1) NOT NULL,
    interv_proteina_c_reactiva TINYINT(1) NOT NULL,
    interv_procalcitonina TINYINT(1) NOT NULL,
    PRIMARY KEY (nuevos)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO registro_a_pacientes_arbol (
    nuevos,
    diagnostico,
    unidad_medica,
    mortalidad,
    total_registros_intervencion,
    total_intervenciones_distintas,
    total_cantidad,
    total_tarifa,
    interv_urgencias_covid,
    interv_hospitalizacion_dia_cama,
    interv_prueba_pcr,
    interv_biometria_hematica,
    interv_quimica_sanguinea,
    interv_dimero_d,
    interv_gasometria,
    interv_radiografia_torax,
    interv_proteina_c_reactiva,
    interv_procalcitonina
)
SELECT
    CAST(TRIM(nuevos) AS CHAR(255)) AS nuevos,
    COALESCE(MAX(NULLIF(TRIM(dx), "")), "SIN_DIAGNOSTICO") AS diagnostico,
    COALESCE(MAX(NULLIF(TRIM(hosp_dest), "")), "SIN_UNIDAD_MEDICA") AS unidad_medica,
    MAX(mortalidad) AS mortalidad,
    COUNT(*) AS total_registros_intervencion,
    COUNT(DISTINCT NULLIF(TRIM(intervencion), "")) AS total_intervenciones_distintas,
    SUM(cantidad) AS total_cantidad,
    SUM(tarifa) AS total_tarifa,
    MAX(CASE WHEN LOWER(COALESCE(intervencion, "")) LIKE "%urgencias valoración pacientes sospechosos y graves por covid-19%" THEN 1 ELSE 0 END) AS interv_urgencias_covid,
    MAX(CASE WHEN LOWER(COALESCE(intervencion, "")) LIKE "%hospitalización día cama%" THEN 1 ELSE 0 END) AS interv_hospitalizacion_dia_cama,
    MAX(CASE WHEN LOWER(COALESCE(intervencion, "")) LIKE "%prueba pcr sars%" THEN 1 ELSE 0 END) AS interv_prueba_pcr,
    MAX(CASE WHEN LOWER(COALESCE(intervencion, "")) LIKE "%biometría hemática completa%" THEN 1 ELSE 0 END) AS interv_biometria_hematica,
    MAX(CASE WHEN LOWER(COALESCE(intervencion, "")) LIKE "%química sanguínea iv%" THEN 1 ELSE 0 END) AS interv_quimica_sanguinea,
    MAX(CASE WHEN LOWER(COALESCE(intervencion, "")) LIKE "%dimero d%" THEN 1 ELSE 0 END) AS interv_dimero_d,
    MAX(CASE WHEN LOWER(COALESCE(intervencion, "")) LIKE "%gasometría%" THEN 1 ELSE 0 END) AS interv_gasometria,
    MAX(CASE WHEN LOWER(COALESCE(intervencion, "")) LIKE "%teleradiografía de tórax%" THEN 1 ELSE 0 END) AS interv_radiografia_torax,
    MAX(CASE WHEN LOWER(COALESCE(intervencion, "")) LIKE "%proteínas c-reactivas%" THEN 1 ELSE 0 END) AS interv_proteina_c_reactiva,
    MAX(CASE WHEN LOWER(COALESCE(intervencion, "")) LIKE "%procalcitonina%" THEN 1 ELSE 0 END) AS interv_procalcitonina
FROM registro_a
WHERE nuevos IS NOT NULL
    AND TRIM(nuevos) <> ""
GROUP BY CAST(TRIM(nuevos) AS CHAR(255));

CREATE INDEX idx_registro_a_pacientes_arbol_mortalidad
    ON registro_a_pacientes_arbol (mortalidad);

CREATE INDEX idx_registro_a_pacientes_arbol_diagnostico
    ON registro_a_pacientes_arbol (diagnostico);

CREATE INDEX idx_registro_a_pacientes_arbol_unidad_medica
    ON registro_a_pacientes_arbol (unidad_medica);
