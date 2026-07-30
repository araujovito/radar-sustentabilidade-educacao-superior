"""Modelo de alerta de deterioração da oferta.

O conjunto vem de `analytics.offer_training_set`, cuja separação é temporal e
cujos atributos são construídos sem informação futura. A ausência de vazamento
é verificada em SQL, por recomputação sobre a série truncada, e não presumida
aqui.

O modelo de referência é uma regressão logística com atributos padronizados:
os coeficientes são legíveis, o que permite explicar cada alerta. A comparação
com um modelo de árvores serve para medir quanto se ganha ao abandonar a
interpretabilidade direta.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Atributos contínuos disponíveis no ano de referência. Nenhum deles resume a
# série inteira: todos vêm de analytics.offer_features, restrita a anos <= t.
NUMERIC_FEATURES = [
    "occupancy_rate",
    "occupancy_rate_lag1",
    "occupancy_change_1y",
    "applications_per_seat",
    "graduation_intensity",
    "low_occupancy_share_to_date",
    "current_low_occupancy_streak",
    "mean_occupancy_to_date",
    "demand_volatility_to_date",
    "enrollment_growth_1y",
    "enrollment_growth_2y",
    "seat_growth_1y",
    "years_observed_to_date",
    "offered_seats",
    "enrollments",
    "institution_offer_count",
    "institution_enrollment_hhi",
]

# Códigos categóricos. TP_CATEGORIA_ADMINISTRATIVA assume 1, 2, 3, 4, 5 e 7 —
# são categorias sem ordem, e tratá-las como número faria o modelo supor um
# efeito monotônico do código, que não significa nada. Modalidade e rede são
# binárias, mas entram pelo mesmo caminho para manter a leitura uniforme.
CATEGORICAL_FEATURES = [
    "teaching_modality",
    "education_network",
    "administrative_category",
]

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Atributo usado na ablação de escala. O rótulo é uma queda de metade do
# estoque de matrículas, e estoques grandes têm dificuldade mecânica de cair
# pela metade. Ranquear apenas por tamanho mede quanto do desempenho vem
# dessa aritmética, e não de sinal de sustentabilidade.
SCALE_FEATURE = "enrollments"

LABEL_COLUMN = "deteriorated"
SPLIT_COLUMN = "split"

# Último ano do treino, reservado para calibrar as probabilidades. Calibrar no
# conjunto de teste inflaria o desempenho; calibrar nos mesmos anos do ajuste
# não corrigiria a deriva temporal, que é justamente o problema observado.
CALIBRATION_YEAR = 2020


@dataclass(frozen=True)
class Evaluation:
    """Desempenho de um modelo em um conjunto."""

    model_name: str
    split: str
    row_count: int
    event_rate: float
    roc_auc: float
    average_precision: float
    # Ausente quando o escore é apenas uma ordenação, e não uma probabilidade:
    # nesse caso não há calibração a medir.
    brier_score: float | None
    precision_at_k: dict[int, float]

    def as_dict(self) -> dict:
        """Serializa para relatório."""
        return {
            "model_name": self.model_name,
            "split": self.split,
            "row_count": self.row_count,
            "event_rate": self.event_rate,
            "roc_auc": self.roc_auc,
            "average_precision": self.average_precision,
            "brier_score": self.brier_score,
            "precision_at_k": {
                str(size): value for size, value in self.precision_at_k.items()
            },
        }


def precision_at_k(
    labels: np.ndarray,
    scores: np.ndarray,
    sizes: tuple[int, ...] = (100, 500, 1000, 5000),
) -> dict[int, float]:
    """Calcula a precisão nas k ofertas de maior risco previsto.

    É a métrica que corresponde ao uso real: uma equipe consegue auditar
    algumas centenas de ofertas, não todas. A ordenação importa mais que a
    probabilidade absoluta.
    """
    order = np.argsort(-scores, kind="stable")
    ranked_labels = labels[order]
    result = {}
    for size in sizes:
        if size > len(ranked_labels):
            continue
        result[size] = float(ranked_labels[:size].mean())
    return result


def build_preprocessor() -> ColumnTransformer:
    """Padroniza os contínuos e codifica os categóricos como indicadores."""
    return ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                Pipeline(
                    [
                        (
                            "imputer",
                            SimpleImputer(strategy="most_frequent"),
                        ),
                        (
                            "encoder",
                            OneHotEncoder(
                                drop="first",
                                handle_unknown="infrequent_if_exist",
                                min_frequency=0.01,
                                sparse_output=False,
                            ),
                        ),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )


def build_reference_model() -> Pipeline:
    """Regressão logística padronizada: o modelo de referência interpretável."""
    return Pipeline(
        [
            ("preprocessor", build_preprocessor()),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    # Sem balanceamento de classe: a taxa de evento observada
                    # é a probabilidade que se quer estimar. Reponderar
                    # distorceria a calibração, que é avaliada adiante.
                    C=1.0,
                    random_state=42,
                ),
            ),
        ]
    )


def build_comparison_model() -> HistGradientBoostingClassifier:
    """Modelo de árvores para medir o custo da interpretabilidade."""
    return HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.05,
        max_depth=5,
        early_stopping=True,
        validation_fraction=0.15,
        random_state=42,
    )


def evaluate(
    model_name: str,
    split: str,
    labels: np.ndarray,
    scores: np.ndarray,
) -> Evaluation:
    """Mede discriminação, calibração e utilidade operacional."""
    # O Brier score mede calibração: quanto menor, mais as probabilidades
    # previstas correspondem às frequências observadas. Só faz sentido quando
    # o escore já é uma probabilidade.
    is_probability = bool(scores.min() >= 0.0 and scores.max() <= 1.0)

    return Evaluation(
        model_name=model_name,
        split=split,
        row_count=int(len(labels)),
        event_rate=float(labels.mean()),
        roc_auc=float(roc_auc_score(labels, scores)),
        average_precision=float(average_precision_score(labels, scores)),
        brier_score=(
            float(brier_score_loss(labels, scores)) if is_probability else None
        ),
        precision_at_k=precision_at_k(labels, scores),
    )


def calibration_table(
    labels: np.ndarray,
    scores: np.ndarray,
    bin_count: int = 10,
) -> list[dict]:
    """Compara probabilidade prevista e frequência observada por decil."""
    edges = np.quantile(scores, np.linspace(0, 1, bin_count + 1))
    edges = np.unique(edges)
    assignments = np.clip(
        np.searchsorted(edges, scores, side="right") - 1,
        0,
        len(edges) - 2,
    )

    rows = []
    for index in range(len(edges) - 1):
        selected = assignments == index
        if not selected.any():
            continue
        rows.append(
            {
                "bin": index,
                "row_count": int(selected.sum()),
                "mean_predicted": float(scores[selected].mean()),
                "observed_rate": float(labels[selected].mean()),
            }
        )
    return rows


def coefficient_table(model: Pipeline) -> list[dict]:
    """Extrai os coeficientes da regressão logística.

    Os contínuos estão padronizados, então o coeficiente indica o efeito de um
    desvio padrão sobre o log-odds. Os categóricos são indicadores, e o
    coeficiente compara a categoria com a de referência omitida. Em nenhum dos
    casos a leitura é causal: os atributos são correlacionados entre si.
    """
    classifier = model.named_steps["classifier"]
    names = model.named_steps["preprocessor"].get_feature_names_out()
    rows = [
        {
            "feature": str(name),
            "coefficient": float(value),
            "odds_ratio": float(np.exp(value)),
        }
        for name, value in zip(names, classifier.coef_[0], strict=True)
    ]
    return sorted(rows, key=lambda row: abs(row["coefficient"]), reverse=True)


def split_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa treino e teste conforme a coluna definida em SQL."""
    train = frame[frame[SPLIT_COLUMN] == "treino"]
    test = frame[frame[SPLIT_COLUMN] == "teste"]
    if train.empty or test.empty:
        raise ValueError("Conjunto sem linhas de treino ou de teste")

    train_years = set(train["reference_year"])
    test_years = set(test["reference_year"])
    if train_years & test_years:
        raise ValueError(
            f"Anos compartilhados entre treino e teste: "
            f"{sorted(train_years & test_years)}"
        )
    if min(test_years) <= max(train_years):
        raise ValueError(
            "A separação não é cronológica: o teste precisa ser posterior"
        )
    return train, test


def run_experiment(frame: pd.DataFrame) -> dict:
    """Treina, avalia fora do tempo e monta o relatório do experimento."""
    train, test = split_frame(frame)

    train_features = train[FEATURE_COLUMNS].astype("float64")
    test_features = test[FEATURE_COLUMNS].astype("float64")
    train_labels = train[LABEL_COLUMN].to_numpy(dtype=bool).astype(int)
    test_labels = test[LABEL_COLUMN].to_numpy(dtype=bool).astype(int)

    reference = build_reference_model()
    reference.fit(train_features, train_labels)

    comparison = build_comparison_model()
    comparison.fit(train_features, train_labels)

    evaluations = []
    for name, model in (
        ("regressao_logistica", reference),
        ("gradient_boosting", comparison),
    ):
        for split_name, features, labels in (
            ("treino", train_features, train_labels),
            ("teste", test_features, test_labels),
        ):
            scores = model.predict_proba(features)[:, 1]
            evaluations.append(evaluate(name, split_name, labels, scores))

    # Calibração fora do tempo. O modelo base é ajustado nos anos anteriores a
    # CALIBRATION_YEAR e a calibração usa apenas esse ano, que é posterior ao
    # ajuste e anterior ao teste. Assim a correção enxerga alguma deriva sem
    # tocar no conjunto de teste.
    fit_mask = train["reference_year"] < CALIBRATION_YEAR
    calibration_mask = train["reference_year"] == CALIBRATION_YEAR
    calibrated_evaluations: list[Evaluation] = []
    calibrated_scores = None
    base_scores = None

    if fit_mask.any() and calibration_mask.any():
        base = build_reference_model()
        base.fit(
            train_features[fit_mask.to_numpy()],
            train_labels[fit_mask.to_numpy()],
        )
        # FrozenEstimator impede que a calibração reajuste o modelo base: ele
        # permanece treinado apenas nos anos anteriores ao de calibração.
        calibrated = CalibratedClassifierCV(
            FrozenEstimator(base), method="isotonic"
        )
        calibrated.fit(
            train_features[calibration_mask.to_numpy()],
            train_labels[calibration_mask.to_numpy()],
        )

        # O modelo base sem calibração entra na comparação para que a diferença
        # isole o efeito da calibração, e não o de treinar com menos anos.
        base_scores = base.predict_proba(test_features)[:, 1]
        calibrated_scores = calibrated.predict_proba(test_features)[:, 1]
        calibrated_evaluations = [
            evaluate(
                "logistica_ajuste_curto", "teste", test_labels, base_scores
            ),
            evaluate(
                "logistica_calibrada", "teste", test_labels, calibrated_scores
            ),
        ]
        evaluations.extend(calibrated_evaluations)

    # Ablação de escala: ranquear apenas pelo inverso do estoque de
    # matrículas, sem treinar nada. Quanto deste desempenho o modelo apenas
    # reproduz? A diferença é o que os atributos de sustentabilidade agregam.
    scale_scores = -test[SCALE_FEATURE].to_numpy(dtype="float64")
    scale_scores = np.nan_to_num(scale_scores, nan=np.nanmin(scale_scores))
    evaluations.append(
        evaluate("apenas_escala", "teste", test_labels, scale_scores)
    )

    reference_scores = reference.predict_proba(test_features)[:, 1]
    comparison_scores = comparison.predict_proba(test_features)[:, 1]

    return {
        "schema_version": 1,
        "train_years": sorted(int(year) for year in set(train["reference_year"])),
        "test_years": sorted(int(year) for year in set(test["reference_year"])),
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "evaluations": [item.as_dict() for item in evaluations],
        "reference_coefficients": coefficient_table(reference),
        "reference_calibration": calibration_table(
            test_labels, reference_scores
        ),
        "comparison_calibration": calibration_table(
            test_labels, comparison_scores
        ),
        "calibration_year": CALIBRATION_YEAR,
        # As duas tabelas abaixo compartilham o mesmo modelo base, de modo que
        # a diferença isola o efeito da calibração.
        "base_calibration": (
            calibration_table(test_labels, base_scores)
            if base_scores is not None
            else []
        ),
        "calibrated_calibration": (
            calibration_table(test_labels, calibrated_scores)
            if calibrated_scores is not None
            else []
        ),
    }


def write_experiment_report(frame: pd.DataFrame, output_path: Path) -> dict:
    """Persiste o relatório do experimento."""
    report = run_experiment(frame)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def load_training_set() -> pd.DataFrame:
    """Lê o conjunto de treino do PostgreSQL."""
    from sqlalchemy import create_engine

    from radar_sustentabilidade.config import Settings

    columns = ", ".join(
        [
            "institution_id",
            "course_id",
            "reference_year",
            SPLIT_COLUMN,
            LABEL_COLUMN,
            "disappeared_from_census",
            *FEATURE_COLUMNS,
        ]
    )
    engine = create_engine(Settings().database_url)
    try:
        return pd.read_sql(
            f"SELECT {columns} FROM analytics.offer_training_set",
            engine,
        )
    finally:
        engine.dispose()
