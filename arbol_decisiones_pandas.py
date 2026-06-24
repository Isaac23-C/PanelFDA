from collections import Counter
from math import ceil
from pathlib import Path
from random import Random

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


COLUMNAS_MODELO = ["horas_estudio", "asistencia", "tareas"]

DATOS_ALUMNOS = {
    "horas_estudio": [10, 15, 12, 18, 20, 16, 11, 14, 12, 10, 8, 2, 1, 4, 5, 3, 13, 9],
    "asistencia": [90, 95, 80, 65, 90, 68, 72, 60, 65, 35, 60, 40, 20, 50, 60, 30, 55, 68],
    "tareas": [1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0],
    "resultado": [
        "Aprobado",
        "Aprobado",
        "Aprobado",
        "Aprobado",
        "Aprobado",
        "Aprobado",
        "Aprobado",
        "Aprobado",
        "Reprobado",
        "Reprobado",
        "Reprobado",
        "Reprobado",
        "Reprobado",
        "Reprobado",
        "Reprobado",
        "Reprobado",
        "Reprobado",
        "Reprobado",
    ],
}

ALUMNO_EJEMPLO = {
    "horas_estudio": 11,
    "asistencia": 85,
    "tareas": 1,
}

ALUMNO_BAJA_ASISTENCIA = {
    "horas_estudio": 18,
    "asistencia": 65,
    "tareas": 1,
}


def cargar_datos() -> pd.DataFrame:
    return pd.DataFrame(DATOS_ALUMNOS)


def separar_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    x = df[COLUMNAS_MODELO]
    y = df["resultado"]
    return x, y


def validar_tamano_prueba(y: pd.Series, tamano_prueba: float) -> None:
    if not 0 < tamano_prueba < 1:
        raise ValueError("tamano_prueba debe estar entre 0 y 1.")

    total_muestras = len(y)
    total_clases = y.nunique()
    filas_prueba = ceil(total_muestras * tamano_prueba)
    filas_entrenamiento = total_muestras - filas_prueba

    if filas_prueba < total_clases or filas_entrenamiento < total_clases:
        raise ValueError(
            "tamano_prueba produce una particion invalida para train_test_split con stratify. "
            f"Se requieren al menos {total_clases} filas por conjunto y se obtuvieron "
            f"{filas_entrenamiento} entrenamiento / {filas_prueba} prueba."
        )


def entrenar_bosque(
    x: pd.DataFrame,
    y: pd.Series,
    tamano_prueba: float = 0.3,
) -> tuple[RandomForestClassifier, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    validar_tamano_prueba(y, tamano_prueba)

    x_entrenamiento, x_prueba, y_entrenamiento, y_prueba = train_test_split(
        x,
        y,
        test_size=tamano_prueba,
        random_state=22,
        stratify=y,
    )

    modelo = RandomForestClassifier(
        n_estimators=3,
        criterion="entropy",
        max_depth=3,
        max_features=1,
        bootstrap=True,
        random_state=42,
    )
    modelo.fit(x_entrenamiento, y_entrenamiento)

    return modelo, x_entrenamiento, x_prueba, y_entrenamiento, y_prueba


def evaluar_modelo(
    modelo: RandomForestClassifier,
    x_prueba: pd.DataFrame,
    y_prueba: pd.Series,
) -> float:
    predicciones = modelo.predict(x_prueba)
    return accuracy_score(y_prueba, predicciones)


def preparar_alumno_df(datos_alumno: dict) -> pd.DataFrame:
    columnas_recibidas = list(datos_alumno.keys())
    faltantes = [columna for columna in COLUMNAS_MODELO if columna not in datos_alumno]
    sobrantes = [columna for columna in columnas_recibidas if columna not in COLUMNAS_MODELO]

    if faltantes or sobrantes:
        raise ValueError(
            "Columnas invalidas para la prediccion. "
            f"Faltantes: {faltantes or 'ninguna'}. "
            f"Sobrantes: {sobrantes or 'ninguna'}."
        )

    return pd.DataFrame([datos_alumno]).reindex(columns=COLUMNAS_MODELO)


def predecir_alumno(
    modelo: RandomForestClassifier,
    datos_alumno: dict,
) -> str:
    alumno_df = preparar_alumno_df(datos_alumno)
    return str(modelo.predict(alumno_df)[0])


def explicar_arbol_individual(
    arbol: DecisionTreeClassifier,
    datos_alumno: dict,
    clases_modelo: list[str],
) -> list[str]:
    alumno_df = preparar_alumno_df(datos_alumno)
    alumno_np = alumno_df.to_numpy()
    indice_nodos = arbol.decision_path(alumno_np).indices
    estructura = arbol.tree_
    explicacion: list[str] = []

    for indice_nodo in indice_nodos:
        indice_variable = estructura.feature[indice_nodo]
        if indice_variable < 0:
            continue

        nombre_variable = COLUMNAS_MODELO[indice_variable]
        umbral = estructura.threshold[indice_nodo]
        valor = alumno_df.iloc[0, indice_variable]
        operador = "<=" if valor <= umbral else ">"
        explicacion.append(f"{nombre_variable} = {valor} {operador} {umbral:.2f}")

    voto_indice = int(arbol.predict(alumno_np)[0])
    explicacion.append(f"Voto del arbol: {clases_modelo[voto_indice]}")
    return explicacion


def obtener_votos_bosque(
    modelo: RandomForestClassifier,
    datos_alumno: dict,
) -> list[dict[str, object]]:
    alumno_df = preparar_alumno_df(datos_alumno)
    alumno_np = alumno_df.to_numpy()
    clases = [str(clase) for clase in modelo.classes_]
    votos: list[dict[str, object]] = []

    for indice, arbol in enumerate(modelo.estimators_, start=1):
        voto_indice = int(arbol.predict(alumno_np)[0])
        votos.append(
            {
                "arbol": indice,
                "voto": clases[voto_indice],
                "reglas": explicar_arbol_individual(arbol, datos_alumno, clases),
            }
        )

    return votos


def resumir_votos(votos: list[dict[str, object]]) -> str:
    conteo = Counter(str(voto["voto"]) for voto in votos)
    return ", ".join(f"{clase}: {total}" for clase, total in sorted(conteo.items()))


def generar_alumnos_aleatorios(
    cantidad: int = 5,
    semilla: int = 2026,
) -> list[dict[str, int]]:
    generador = Random(semilla)
    alumnos: list[dict[str, int]] = []

    for _ in range(cantidad):
        alumnos.append(
            {
                "horas_estudio": generador.randint(1, 20),
                "asistencia": generador.randint(20, 100),
                "tareas": generador.randint(0, 1),
            }
        )

    return alumnos


def guardar_bosque(
    modelo: RandomForestClassifier,
    ruta_salida: Path,
) -> None:
    if plt is None:
        return

    total_arboles = len(modelo.estimators_)
    fig, ejes = plt.subplots(1, total_arboles, figsize=(7 * total_arboles, 7))
    if total_arboles == 1:
        ejes = [ejes]

    for indice, (ax, arbol) in enumerate(zip(ejes, modelo.estimators_, strict=True), start=1):
        plot_tree(
            arbol,
            feature_names=COLUMNAS_MODELO,
            class_names=[str(clase) for clase in modelo.classes_],
            filled=True,
            rounded=True,
            ax=ax,
        )
        ax.set_title(f"Arbol {indice}")

    fig.tight_layout()
    fig.savefig(ruta_salida, dpi=200)
    plt.close(fig)


def imprimir_reporte_alumno(
    titulo: str,
    modelo: RandomForestClassifier,
    datos_alumno: dict,
) -> None:
    votos = obtener_votos_bosque(modelo, datos_alumno)
    resultado_final = predecir_alumno(modelo, datos_alumno)

    print(titulo)
    print(pd.DataFrame([datos_alumno]).to_string(index=False))
    print()
    for voto in votos:
        print(f"VOTO DEL ARBOL {voto['arbol']}: {voto['voto']}")
        for regla in voto["reglas"]:
            print(f"- {regla}")
        print()

    print(f"CONTEO DE VOTOS: {resumir_votos(votos)}")
    print(f"RESULTADO FINAL DEL BOSQUE: {resultado_final}")


def main() -> None:
    df = cargar_datos()
    x, y = separar_xy(df)

    tamano_prueba = 0.3
    modelo, x_entrenamiento, x_prueba, y_entrenamiento, y_prueba = entrenar_bosque(
        x,
        y,
        tamano_prueba=tamano_prueba,
    )

    precision = evaluar_modelo(modelo, x_prueba, y_prueba)
    salida_bosque = Path(__file__).resolve().with_name("bosque_decision_alumnos.png")
    guardar_bosque(modelo, salida_bosque)

    df_entrenamiento = x_entrenamiento.assign(resultado=y_entrenamiento).sort_index()

    print("DATASET COMPLETO")
    print(df.to_string(index=False))
    print()

    print("FILAS USADAS PARA ENTRENAMIENTO")
    print(df_entrenamiento.to_string(index=False))
    print()

    print("VARIABLES X")
    print(x.to_string(index=False))
    print()

    print("VARIABLE Y")
    print(y.to_string(index=False))
    print()

    print(f"Tamanio de prueba usado en train_test_split: {tamano_prueba}")
    print(f"Filas de entrenamiento: {len(x_entrenamiento)}")
    print(f"Filas de prueba: {len(x_prueba)}")
    print(f"Precision del modelo: {precision:.2f}")
    print("Configuracion del bosque: 3 arboles, entropy, profundidad maxima 3, max_features=1")
    print()

    imprimir_reporte_alumno("DATOS DEL ALUMNO A PREDECIR", modelo, ALUMNO_EJEMPLO)
    print()
    imprimir_reporte_alumno(
        "CASO: BAJA ASISTENCIA, MUCHAS HORAS Y TAREAS ENTREGADAS",
        modelo,
        ALUMNO_BAJA_ASISTENCIA,
    )
    print()

    alumnos_aleatorios = generar_alumnos_aleatorios(cantidad=5, semilla=2026)
    for indice, alumno in enumerate(alumnos_aleatorios, start=1):
        imprimir_reporte_alumno(f"ALUMNO ALEATORIO {indice}", modelo, alumno)
        if indice < len(alumnos_aleatorios):
            print()

    if plt is not None:
        print()
        print(f"Imagen del bosque guardada en: {salida_bosque}")


if __name__ == "__main__":
    main()
