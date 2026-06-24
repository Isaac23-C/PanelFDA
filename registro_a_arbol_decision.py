from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mysql.connector
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier, plot_tree


DB_CONFIG = {
    "user": "root",
    "password": "root",
    "host": "127.0.0.1",
    "port": 8889,
    "database": "covid_19pruebas",
}

CATEGORICAL_FEATURES = ["diagnostico", "unidad_medica"]
INTERVENTION_FEATURES = [
    "interv_urgencias_covid",
    "interv_hospitalizacion_dia_cama",
    "interv_prueba_pcr",
    "interv_biometria_hematica",
    "interv_quimica_sanguinea",
    "interv_dimero_d",
    "interv_gasometria",
    "interv_radiografia_torax",
    "interv_proteina_c_reactiva",
    "interv_procalcitonina",
]
TARGET = "mortalidad"


def load_dataset() -> pd.DataFrame:
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        query = """
            SELECT
                diagnostico,
                unidad_medica,
                interv_urgencias_covid,
                interv_hospitalizacion_dia_cama,
                interv_prueba_pcr,
                interv_biometria_hematica,
                interv_quimica_sanguinea,
                interv_dimero_d,
                interv_gasometria,
                interv_radiografia_torax,
                interv_proteina_c_reactiva,
                interv_procalcitonina,
                mortalidad
            FROM registro_a_pacientes_arbol
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def build_pipeline() -> Pipeline:
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="SIN_VALOR")),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="infrequent_if_exist",
                    min_frequency=100,
                    sparse_output=False,
                ),
            ),
        ]
    )

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
            ("intervention", numeric_pipeline, INTERVENTION_FEATURES),
        ]
    )

    classifier = DecisionTreeClassifier(
        criterion="entropy",
        max_depth=4,
        min_samples_leaf=100,
        class_weight="balanced",
        random_state=42,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )


def save_tree_image(pipeline: Pipeline, output_path: Path) -> None:
    preprocessor: ColumnTransformer = pipeline.named_steps["preprocessor"]
    classifier: DecisionTreeClassifier = pipeline.named_steps["classifier"]

    feature_names = preprocessor.get_feature_names_out()

    fig, ax = plt.subplots(figsize=(28, 16))
    plot_tree(
        classifier,
        feature_names=feature_names,
        class_names=["Sobrevive", "Mortalidad"],
        filled=True,
        rounded=True,
        fontsize=8,
        ax=ax,
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def print_top_features(pipeline: Pipeline, top_n: int = 15) -> None:
    preprocessor: ColumnTransformer = pipeline.named_steps["preprocessor"]
    classifier: DecisionTreeClassifier = pipeline.named_steps["classifier"]

    feature_names = preprocessor.get_feature_names_out()
    importances = classifier.feature_importances_

    importance_df = (
        pd.DataFrame({"feature": feature_names, "importance": importances})
        .sort_values("importance", ascending=False)
    )

    print("TOP VARIABLES DEL ARBOL")
    print(importance_df.head(top_n).to_string(index=False))
    print()


def format_rule(feature_name: str, threshold: float, goes_left: bool) -> str:
    if feature_name.startswith("categorical__"):
        encoded_name = feature_name.split("__", maxsplit=1)[1]

        if encoded_name.startswith("diagnostico_"):
            readable_name = "diagnóstico"
            category_value = encoded_name.removeprefix("diagnostico_")
        elif encoded_name.startswith("unidad_medica_"):
            readable_name = "unidad médica"
            category_value = encoded_name.removeprefix("unidad_medica_")
        else:
            parts = encoded_name.split("_", maxsplit=1)
            readable_name = parts[0].replace("_", " ")
            category_value = parts[1] if len(parts) > 1 else encoded_name

        if goes_left:
            return f"{readable_name} no es {category_value}"
        return f"{readable_name} es {category_value}"

    readable_name = feature_name.split("__", maxsplit=1)[1].replace("_", " ")
    operator = "<=" if goes_left else ">"
    return f"{readable_name} {operator} {threshold:.2f}"


def describe_tree_leaves(pipeline: Pipeline, top_n: int = 8) -> None:
    preprocessor: ColumnTransformer = pipeline.named_steps["preprocessor"]
    classifier: DecisionTreeClassifier = pipeline.named_steps["classifier"]
    feature_names = list(preprocessor.get_feature_names_out())
    tree = classifier.tree_

    leaf_descriptions: list[dict[str, object]] = []

    def walk(node_id: int, conditions: list[str]) -> None:
        left_child = tree.children_left[node_id]
        right_child = tree.children_right[node_id]

        if left_child == right_child:
            class_values = tree.value[node_id][0]
            total_weight = class_values.sum()
            mortalidad_count = class_values[1] if len(class_values) > 1 else 0
            prob_mortalidad = mortalidad_count / total_weight if total_weight else 0.0
            prediction = "mortalidad" if prob_mortalidad >= 0.5 else "no mortalidad"
            leaf_descriptions.append(
                {
                    "conditions": list(conditions),
                    "samples": int(tree.n_node_samples[node_id]),
                    "prob_mortalidad": prob_mortalidad,
                    "prediction": prediction,
                }
            )
            return

        feature_name = feature_names[tree.feature[node_id]]
        threshold = tree.threshold[node_id]

        walk(
            left_child,
            conditions + [format_rule(feature_name, threshold, goes_left=True)],
        )
        walk(
            right_child,
            conditions + [format_rule(feature_name, threshold, goes_left=False)],
        )

    walk(0, [])

    ordered = sorted(
        leaf_descriptions,
        key=lambda item: (item["prob_mortalidad"], item["samples"]),
        reverse=True,
    )

    print("REGLAS REALES DEL ARBOL")
    for index, leaf in enumerate(ordered[:top_n], start=1):
        conditions = leaf["conditions"]
        if conditions:
            joined_conditions = " y ".join(conditions)
        else:
            joined_conditions = "sin condiciones"

        probability = float(leaf["prob_mortalidad"]) * 100
        samples = int(leaf["samples"])
        prediction = str(leaf["prediction"])
        print(
            f"{index}. Si {joined_conditions}, la probabilidad de mortalidad es "
            f"{probability:.1f}% ({samples} pacientes en la hoja, predicción: {prediction})."
        )
    print()


def main() -> None:
    df = load_dataset()
    x = df[CATEGORICAL_FEATURES + INTERVENTION_FEATURES]
    y = df[TARGET]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.3,
        random_state=42,
        stratify=y,
    )

    pipeline = build_pipeline()
    pipeline.fit(x_train, y_train)

    y_pred = pipeline.predict(x_test)
    y_prob = pipeline.predict_proba(x_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred)

    output_path = Path(__file__).resolve().with_name("registro_a_arbol_decision.png")
    save_tree_image(pipeline, output_path)

    print("MODELO: ARBOL DE DECISION SOBRE registro_a_pacientes_arbol")
    print(f"Filas totales: {len(df)}")
    print(f"Filas entrenamiento: {len(x_train)}")
    print(f"Filas prueba: {len(x_test)}")
    print(f"Pacientes con mortalidad: {int(y.sum())}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"ROC AUC: {auc:.4f}")
    print()

    print("MATRIZ DE CONFUSION")
    print(cm)
    print()

    print("REPORTE DE CLASIFICACION")
    print(classification_report(y_test, y_pred, digits=4))

    print_top_features(pipeline)
    describe_tree_leaves(pipeline)
    print(f"Imagen del arbol guardada en: {output_path}")


if __name__ == "__main__":
    main()
