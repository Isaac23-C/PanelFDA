from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import streamlit as st

from arbol_decisiones_pandas import (
    cargar_datos,
    entrenar_bosque,
    evaluar_modelo,
    obtener_votos_bosque,
    predecir_alumno,
    separar_xy,
)


APP_DIR = Path(__file__).resolve().parent
IMAGE_ALUMNOS = APP_DIR / "bosque_decision_alumnos.png"
IMAGE_MORTALIDAD = APP_DIR / "registro_a_arbol_decision.png"


@dataclass
class ClinicalPrediction:
    risk_score: float
    mortality_risk: str
    estimated_stay_days: float
    requires_tube: str
    summary: str
    factors: list[str]


INTERVENTION_PROFILES = {
    "Ninguna": {"severity": 0.10, "tube": False},
    "Oxígeno": {"severity": 0.42, "tube": False},
    "Intubación": {"severity": 0.78, "tube": True},
    "Ventilación Mecánica": {"severity": 0.92, "tube": True},
}

RISK_COLORS = {
    "BAJO": "#2E8B57",
    "MEDIO": "#D97706",
    "ALTO": "#C0392B",
}


def normalize_text(value: str) -> str:
    lowered = value.strip().lower()
    replacements = str.maketrans(
        {
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
            "ü": "u",
            "ñ": "n",
        }
    )
    return lowered.translate(replacements)


def detect_diagnosis_weight(diagnosis: str) -> tuple[float, list[str]]:
    normalized = normalize_text(diagnosis)
    score = 0.0
    factors: list[str] = []

    if any(keyword in normalized for keyword in ("covid", "sars", "coronavirus")):
        score += 0.18
        factors.append("Diagnóstico respiratorio compatible con COVID-19.")

    if any(keyword in normalized for keyword in ("neumonia", "hipox", "dificultad respiratoria")):
        score += 0.18
        factors.append("El diagnóstico sugiere compromiso pulmonar.")

    if any(keyword in normalized for keyword in ("sepsis", "choque", "falla multiorganica")):
        score += 0.20
        factors.append("Se detectaron términos asociados a gravedad sistémica.")

    return min(score, 0.42), factors


def infer_unit_from_level(level: int, state: str, municipality: str) -> tuple[str, list[str]]:
    normalized_state = normalize_text(state)
    normalized_municipality = normalize_text(municipality)
    factors: list[str] = []

    if level >= 4:
        unit = "UCI COVID"
        factors.append("Nivel de atención alto, compatible con manejo intensivo.")
    elif level == 3:
        unit = "Hospitalización COVID"
        factors.append("Nivel de atención intermedio con requerimiento hospitalario.")
    elif "mexico" in normalized_state or "cdmx" in normalized_state:
        unit = f"Urgencias {municipality.strip() or 'COVID'}"
        factors.append("Procedencia urbana; se asume atención por urgencias.")
    else:
        unit = f"Unidad General {municipality.strip() or state.strip() or 'COVID'}"

    if re.search(r"(iztapalapa|gustavo a madero|coyoacan|cuauhtemoc)", normalized_municipality):
        factors.append("Municipio metropolitano asociado a atención de alta demanda.")

    return unit, factors


def predict_clinical_case(
    age: int,
    gender: str,
    attention_level: int,
    diagnosis: str,
    state: str,
    municipality: str,
    intervention: str,
) -> ClinicalPrediction:
    del gender

    profile = INTERVENTION_PROFILES[intervention]
    diagnosis_score, diagnosis_factors = detect_diagnosis_weight(diagnosis)
    unit, unit_factors = infer_unit_from_level(attention_level, state, municipality)

    age_score = min(max((age - 35) / 70, 0), 0.35)
    level_score = min(attention_level / 10, 0.30)
    intervention_score = profile["severity"]
    location_score = 0.06 if "covid" in normalize_text(unit) else 0.02

    total_score = min(age_score + level_score + intervention_score + diagnosis_score + location_score, 0.99)

    if total_score < 0.45:
        risk = "BAJO"
    elif total_score < 0.72:
        risk = "MEDIO"
    else:
        risk = "ALTO"

    requires_tube = "Sí" if profile["tube"] or total_score >= 0.80 else "No"
    estimated_stay_days = round(1.8 + total_score * 5.8 + attention_level * 0.35, 1)

    factors = [
        f"Edad capturada: {age} años.",
        f"Unidad inferida para el caso: {unit}.",
        f"Intervención principal reportada: {intervention}.",
        *diagnosis_factors,
        *unit_factors,
    ]

    summary = (
        f"Riesgo {risk.lower()} con puntaje clínico {total_score:.2f}. "
        f"El cálculo pondera edad, nivel de atención, intervención y severidad del diagnóstico."
    )

    return ClinicalPrediction(
        risk_score=total_score,
        mortality_risk=risk,
        estimated_stay_days=estimated_stay_days,
        requires_tube=requires_tube,
        summary=summary,
        factors=factors,
    )


@st.cache_resource
def load_student_model():
    df = cargar_datos()
    x, y = separar_xy(df)
    model, x_train, x_test, y_train, y_test = entrenar_bosque(x, y, tamano_prueba=0.3)
    accuracy = evaluar_modelo(model, x_test, y_test)
    return {
        "dataset": df,
        "model": model,
        "accuracy": accuracy,
        "train_rows": len(x_train),
        "test_rows": len(x_test),
    }


def render_card(title: str, value: str, color: str) -> None:
    st.markdown(
        f"""
        <div style="
            border: 1px solid #d8dee9;
            border-radius: 14px;
            padding: 18px 16px;
            background: white;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
            text-align: center;
            min-height: 148px;
        ">
            <div style="font-size: 1.0rem; color: #334155; margin-bottom: 20px;">{title}</div>
            <div style="font-size: 2rem; font-weight: 700; color: {color};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_student_tab() -> None:
    resources = load_student_model()
    model = resources["model"]

    st.subheader("Predicción de Rendimiento Escolar")
    st.caption("Modelo basado en el bosque de decisión local entrenado con horas de estudio, asistencia y tareas.")

    with st.form("student_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            hours = st.number_input("Horas de Estudio", min_value=1, max_value=30, value=14, step=1)
        with col2:
            attendance = st.number_input("Asistencia (%)", min_value=0, max_value=100, value=50, step=1)
        with col3:
            homework = st.selectbox("Entregó Tareas", options=[1, 0], format_func=lambda v: "Sí (1)" if v == 1 else "No (0)")

        submitted = st.form_submit_button("Evaluar Alumno", use_container_width=True)

    if submitted:
        student_data = {
            "horas_estudio": int(hours),
            "asistencia": int(attendance),
            "tareas": int(homework),
        }
        result = predecir_alumno(model, student_data).upper()
        votes = obtener_votos_bosque(model, student_data)
        result_color = "#2E8B57" if result == "APROBADO" else "#C0392B"

        st.markdown(
            f"""
            <div style="
                margin-top: 10px;
                margin-bottom: 18px;
                padding: 18px;
                border-radius: 14px;
                background: {result_color};
                color: white;
                text-align: center;
                font-size: 1.9rem;
                font-weight: 700;
            ">
                Resultado Predicho: {result}
            </div>
            """,
            unsafe_allow_html=True,
        )

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Precisión del modelo", f"{resources['accuracy']:.2%}")
        metric_col2.metric("Filas de entrenamiento", str(resources["train_rows"]))
        metric_col3.metric("Filas de prueba", str(resources["test_rows"]))

        with st.expander("Explicación del bosque"):
            for vote in votes:
                st.markdown(f"**Árbol {vote['arbol']}**: {vote['voto']}")
                for rule in vote["reglas"]:
                    st.write(f"- {rule}")

        vote_summary = {}
        for vote in votes:
            vote_summary[vote["voto"]] = vote_summary.get(vote["voto"], 0) + 1
        st.caption(
            "Conteo de votos: "
            + ", ".join(f"{label}: {count}" for label, count in sorted(vote_summary.items()))
        )

    image_col, info_col = st.columns([1.2, 1.0])
    with image_col:
        if IMAGE_ALUMNOS.exists():
            st.image(str(IMAGE_ALUMNOS), caption="Bosque de decisión generado localmente", use_container_width=True)
    with info_col:
        st.markdown("**Variables del modelo**")
        st.write("- Horas de estudio")
        st.write("- Asistencia")
        st.write("- Entrega de tareas")
        st.markdown("**Dataset base**")
        st.dataframe(resources["dataset"], use_container_width=True, hide_index=True)


def render_clinical_tab() -> None:
    st.subheader("Pronóstico Clínico COVID-19")
    st.caption("Panel de simulación con métricas resumidas inspirado en el flujo clínico del árbol local.")

    with st.form("clinical_form"):
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        with row1_col1:
            age = st.number_input("Edad", min_value=0, max_value=110, value=45, step=1)
        with row1_col2:
            gender = st.selectbox("Género", ["Hombre", "Mujer"])
        with row1_col3:
            attention_level = st.number_input("Nivel de atención", min_value=1, max_value=5, value=2, step=1)

        row2_col1, row2_col2, row2_col3 = st.columns(3)
        with row2_col1:
            diagnosis = st.text_input("Diagnóstico", value="COVID-19")
        with row2_col2:
            state = st.text_input("Estado", value="CIUDAD DE MÉXICO")
        with row2_col3:
            municipality = st.text_input("Municipio", value="IZTAPALAPA")

        intervention = st.selectbox(
            "Intervención",
            ["Ninguna", "Oxígeno", "Intubación", "Ventilación Mecánica"],
            index=1,
        )

        submitted = st.form_submit_button("Generar Pronóstico Clínico", use_container_width=True)

    if submitted:
        prediction = predict_clinical_case(
            age=int(age),
            gender=gender,
            attention_level=int(attention_level),
            diagnosis=diagnosis,
            state=state,
            municipality=municipality,
            intervention=intervention,
        )

        card1, card2, card3 = st.columns(3)
        with card1:
            render_card("Requerimiento de Tubo", prediction.requires_tube.upper(), "#C0392B" if prediction.requires_tube == "Sí" else "#2E8B57")
        with card2:
            render_card("Estancia Estimada", f"{prediction.estimated_stay_days} días", "#1F2937")
        with card3:
            render_card("Riesgo de Mortalidad", prediction.mortality_risk, RISK_COLORS[prediction.mortality_risk])

        st.progress(prediction.risk_score, text=f"Puntaje clínico: {prediction.risk_score:.0%}")
        st.info(prediction.summary)

        with st.expander("Factores considerados"):
            for factor in prediction.factors:
                st.write(f"- {factor}")

    image_col, detail_col = st.columns([1.2, 1.0])
    with image_col:
        if IMAGE_MORTALIDAD.exists():
            st.image(str(IMAGE_MORTALIDAD), caption="Árbol clínico generado localmente", use_container_width=True)
    with detail_col:
        st.markdown("**Entradas clínicas del panel**")
        st.write("- Edad")
        st.write("- Nivel de atención")
        st.write("- Diagnóstico")
        st.write("- Estado y municipio")
        st.write("- Intervención reportada")
        st.markdown("**Referencia del cálculo**")
        st.write(
            "La simulación pondera severidad de intervención, diagnóstico y contexto de atención "
            "para devolver una salida estilo dashboard."
        )


def main() -> None:
    st.set_page_config(
        page_title="Panel de Modelos Predictivos",
        page_icon="📊",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 12px 12px 0 0;
            padding: 0.8rem 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Panel de Modelos Predictivos")
    st.caption("Replica funcional de los paneles de referencia usando los modelos y entregables presentes en este workspace.")

    tab_students, tab_clinical = st.tabs(["Modelo Alumnos", "Modelo Clínico COVID-19"])
    with tab_students:
        render_student_tab()
    with tab_clinical:
        render_clinical_tab()


if __name__ == "__main__":
    main()
