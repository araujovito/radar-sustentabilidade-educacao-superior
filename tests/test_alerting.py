import numpy as np
import pandas as pd
import pytest

from radar_sustentabilidade.alerting import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    LABEL_COLUMN,
    NUMERIC_FEATURES,
    build_reference_model,
    calibration_table,
    coefficient_table,
    evaluate,
    explain_predictions,
    precision_at_k,
    rolling_window_stability,
    split_frame,
)


def test_precision_at_k_ranks_by_descending_score() -> None:
    labels = np.array([0, 1, 1, 0, 1, 0])
    # As duas maiores pontuações correspondem a rótulos positivos.
    scores = np.array([0.1, 0.9, 0.8, 0.2, 0.4, 0.05])

    result = precision_at_k(labels, scores, sizes=(2, 4))

    assert result[2] == 1.0
    assert result[4] == pytest.approx(0.75)


def test_precision_at_k_skips_sizes_larger_than_the_sample() -> None:
    labels = np.array([1, 0])
    scores = np.array([0.9, 0.1])

    result = precision_at_k(labels, scores, sizes=(1, 100))

    assert set(result) == {1}


def test_evaluate_omits_brier_score_for_pure_rankings() -> None:
    labels = np.array([0, 1, 1, 0])
    ranking = np.array([-500.0, -10.0, -20.0, -900.0])

    result = evaluate("apenas_escala", "teste", labels, ranking)

    # Uma ordenação não é probabilidade: não há calibração a medir.
    assert result.brier_score is None
    assert result.as_dict()["brier_score"] is None


def test_evaluate_reports_brier_score_for_probabilities() -> None:
    labels = np.array([0, 1, 1, 0])
    probabilities = np.array([0.1, 0.8, 0.7, 0.2])

    result = evaluate("modelo", "teste", labels, probabilities)

    assert result.brier_score is not None
    assert result.brier_score >= 0


def test_calibration_table_compares_predicted_against_observed() -> None:
    scores = np.linspace(0.0, 1.0, 100)
    # Rótulo determinístico acima da metade: os últimos grupos devem observar
    # frequência 1 e os primeiros, 0.
    labels = (scores > 0.5).astype(int)

    rows = calibration_table(labels, scores, bin_count=4)

    assert sum(row["row_count"] for row in rows) == 100
    assert rows[0]["observed_rate"] == 0.0
    assert rows[-1]["observed_rate"] == 1.0


def make_frame(years: list[int], rows_per_year: int = 40) -> pd.DataFrame:
    generator = np.random.default_rng(7)
    records = []
    for year in years:
        for index in range(rows_per_year):
            records.append(
                {
                    "reference_year": year,
                    "split": (
                        "treino" if year <= 2020 else "teste"
                    ),
                    "deteriorated": bool(index % 4 == 0),
                    **{
                        name: float(generator.normal())
                        for name in NUMERIC_FEATURES
                    },
                    "teaching_modality": float(1 + index % 2),
                    "education_network": float(1 + index % 2),
                    "administrative_category": float(
                        [1, 2, 4, 5][index % 4]
                    ),
                }
            )
    return pd.DataFrame.from_records(records)


def test_split_frame_rejects_years_shared_between_train_and_test() -> None:
    frame = make_frame([2019, 2020])
    frame.loc[frame["reference_year"] == 2020, "split"] = "teste"
    leaked = frame.copy()
    leaked.loc[leaked.index[:5], "split"] = "teste"
    leaked.loc[leaked.index[:5], "reference_year"] = 2019

    with pytest.raises(ValueError, match="Anos compartilhados"):
        split_frame(leaked)


def test_split_frame_requires_the_test_years_to_come_after_training() -> None:
    frame = make_frame([2019, 2021])
    # Inverte a atribuição: o teste passaria a ser anterior ao treino.
    frame["split"] = np.where(
        frame["reference_year"] == 2019, "teste", "treino"
    )

    with pytest.raises(ValueError, match="não é cronológica"):
        split_frame(frame)


def test_split_frame_accepts_a_chronological_split() -> None:
    train, test = split_frame(make_frame([2019, 2020, 2021]))

    assert set(train["reference_year"]) == {2019, 2020}
    assert set(test["reference_year"]) == {2021}


def test_categorical_codes_are_encoded_as_indicators() -> None:
    frame = make_frame([2019, 2020, 2021])
    model = build_reference_model()
    train = frame[frame["split"] == "treino"]
    model.fit(
        train[FEATURE_COLUMNS].astype("float64"),
        train["deteriorated"].to_numpy(dtype=bool).astype(int),
    )

    features = [row["feature"] for row in coefficient_table(model)]

    # A categoria administrativa não é ordinal: precisa virar indicadores, e
    # não entrar como um único coeficiente sobre o código numérico.
    assert "categorical__administrative_category" not in features
    expanded = [
        name
        for name in features
        if name.startswith("categorical__administrative_category_")
    ]
    assert len(expanded) >= 2
    # Todo atributo contínuo permanece com um coeficiente próprio.
    for name in NUMERIC_FEATURES:
        assert f"numeric__{name}" in features


def test_feature_columns_are_the_union_without_duplicates() -> None:
    assert FEATURE_COLUMNS == NUMERIC_FEATURES + CATEGORICAL_FEATURES
    assert len(FEATURE_COLUMNS) == len(set(FEATURE_COLUMNS))


def fitted_model(frame: pd.DataFrame) -> object:
    model = build_reference_model()
    train = frame[frame["split"] == "treino"]
    model.fit(
        train[FEATURE_COLUMNS].astype("float64"),
        train[LABEL_COLUMN].to_numpy(dtype=bool).astype(int),
    )
    return model


def test_explanations_decompose_the_prediction_exactly() -> None:
    frame = make_frame([2019, 2020, 2021])
    model = fitted_model(frame)
    test = frame[frame["split"] == "teste"][FEATURE_COLUMNS].astype("float64")

    explanations = explain_predictions(model, test.head(6), top_n=99)
    predicted = model.predict_proba(test.head(6))[:, 1]

    # A decomposição da regressão logística é exata: intercepto mais a soma
    # das contribuições reproduz o log-odds, e portanto a probabilidade.
    for explanation, probability in zip(explanations, predicted, strict=True):
        total = explanation["intercept"] + sum(
            item["contribution"] for item in explanation["top_contributions"]
        )
        assert total == pytest.approx(explanation["log_odds"], abs=1e-9)
        assert explanation["predicted_probability"] == pytest.approx(
            probability, abs=1e-9
        )


def test_explanations_return_the_largest_contributions_first() -> None:
    frame = make_frame([2019, 2020, 2021])
    model = fitted_model(frame)
    test = frame[frame["split"] == "teste"][FEATURE_COLUMNS].astype("float64")

    explanation = explain_predictions(model, test.head(1), top_n=4)[0]
    magnitudes = [
        abs(item["contribution"]) for item in explanation["top_contributions"]
    ]

    assert len(magnitudes) == 4
    assert magnitudes == sorted(magnitudes, reverse=True)


def test_stability_reports_overlap_and_separates_sign_flips() -> None:
    frame = make_frame([2016, 2017, 2018, 2019, 2020, 2021])
    frame["split"] = np.where(
        frame["reference_year"] <= 2020, "treino", "teste"
    )

    result = rolling_window_stability(frame, window_size=3, top_k=10)

    # Cinco anos de treino em janelas de três geram três janelas.
    assert [window["window"] for window in result["windows"]] == [
        "2016-2018",
        "2017-2019",
        "2018-2020",
    ]
    assert len(result["consecutive_top_k_overlap"]) == 2
    for overlap in result["consecutive_top_k_overlap"]:
        assert 0.0 <= overlap["jaccard"] <= 1.0

    # Um atributo não pode ser classificado como estável e instável ao mesmo
    # tempo: a magnitude acompanha cada caso para separar instabilidade real
    # de coeficiente que apenas oscila em torno de zero.
    flipping = {row["feature"] for row in result["sign_flipping_features"]}
    stable = {row["feature"] for row in result["sign_stable_features"]}
    assert not flipping & stable
    for row in result["sign_flipping_features"]:
        assert row["max_absolute_coefficient"] >= 0


def test_stability_requires_more_than_one_window() -> None:
    frame = make_frame([2019, 2020, 2021])
    frame["split"] = np.where(
        frame["reference_year"] <= 2020, "treino", "teste"
    )

    with pytest.raises(ValueError, match="ao menos duas janelas"):
        rolling_window_stability(frame, window_size=2)
