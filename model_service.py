from typing import Any, Dict, Optional
import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

FEATURE_COLUMNS = ["hemo", "al", "sg", "sc", "pcv", "htn"]
TARGET_COLUMN = "classification"
MODEL_PATH = os.path.join("model", "model.pkl")


def _normalize_binary(value: Any) -> Optional[int]:
    if pd.isna(value):
        return None

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (int, float)):
        return 1 if float(value) > 0 else 0

    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"yes", "y", "true", "t", "1", "positive", "present"}:
            return 1
        if text in {"no", "n", "false", "f", "0", "negative", "absent"}:
            return 0

    return None


def _clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()

    for col in cleaned.columns:
        if pd.api.types.is_object_dtype(cleaned[col]) or pd.api.types.is_string_dtype(cleaned[col]):
            cleaned[col] = cleaned[col].astype("string").str.strip()

    cleaned.replace("?", pd.NA, inplace=True)
    cleaned.drop(columns=["id"], inplace=True, errors="ignore")

    numeric_cols = [
        "age", "bp", "sg", "al", "su",
        "bgr", "bu", "sc", "sod", "pot",
        "hemo", "pcv", "wc", "rc"
    ]

    for col in numeric_cols:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    for col in cleaned.columns:
        if pd.api.types.is_numeric_dtype(cleaned[col]):
            cleaned[col] = cleaned[col].fillna(cleaned[col].median())
        else:
            cleaned[col] = cleaned[col].fillna(cleaned[col].mode()[0])

    cleaned["htn"] = cleaned["htn"].apply(_normalize_binary)
    cleaned["classification"] = cleaned["classification"].astype(str).str.strip().str.lower()

    return cleaned


def prepare_feature_frame(payload: Dict[str, Any], feature_medians: Optional[Dict[str, float]] = None) -> pd.DataFrame:
    frame = pd.DataFrame([payload])
    frame = frame.reindex(columns=FEATURE_COLUMNS, fill_value=None)

    for col in ["hemo", "al", "sg", "sc", "pcv"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")

    frame["htn"] = frame["htn"].apply(_normalize_binary)

    if feature_medians:
        for col, median_value in feature_medians.items():
            frame[col] = frame[col].fillna(median_value)
    else:
        for col in ["hemo", "al", "sg", "sc", "pcv"]:
            frame[col] = frame[col].fillna(frame[col].median())

    frame["htn"] = frame["htn"].fillna(0)

    return frame

def train_and_save_model(model_path: str = MODEL_PATH) -> Dict[str, Any]:
    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    df = _clean_dataset(pd.read_csv("dataset/kidney_disease.csv"))

    features = df[FEATURE_COLUMNS].copy()
    target = df[TARGET_COLUMN].astype(str).str.strip().str.lower()

    target_encoder = LabelEncoder()
    encoded_target = target_encoder.fit_transform(target)

    feature_medians = {
        col: float(features[col].median())
        for col in ["hemo", "al", "sg", "sc", "pcv"]
    }

    for col in ["hemo", "al", "sg", "sc", "pcv"]:
        features[col] = features[col].fillna(feature_medians[col])

    features["htn"] = features["htn"].fillna(0)

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        encoded_target,
        test_size=0.2,
        random_state=42,
        stratify=encoded_target,
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced_subsample",
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    artifact = {
        "model": model,
        "feature_columns": FEATURE_COLUMNS,
        "feature_medians": feature_medians,
        "target_encoder": target_encoder,
        "accuracy": float(accuracy),
    }

    joblib.dump(artifact, model_path)
    return artifact


def load_model_artifact(model_path: str = MODEL_PATH) -> Dict[str, Any]:
    if not os.path.exists(model_path):
        return train_and_save_model(model_path)

    artifact = joblib.load(model_path)
    if isinstance(artifact, dict) and "model" in artifact:
        return artifact

    raise TypeError("The saved model artifact is not in the expected format")


def predict_with_model(payload: Dict[str, Any], artifact: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    artifact = artifact or load_model_artifact()

    frame = prepare_feature_frame(payload, artifact.get("feature_medians"))
    frame = frame[artifact.get("feature_columns", FEATURE_COLUMNS)]

    model = artifact["model"]
    target_encoder = artifact["target_encoder"]

    probas = model.predict_proba(frame)[0]
    prediction_index = int(model.predict(frame)[0])
    predicted_label = str(target_encoder.inverse_transform([prediction_index])[0]).strip().lower()
    confidence = float(probas[list(model.classes_).index(prediction_index)] * 100)

    # Probability always means estimated probability of the CKD class,
    # not probability of whichever class happened to be predicted.
    encoder_classes = [str(label).strip().lower() for label in target_encoder.classes_]
    ckd_index = next(
        (idx for idx, label in enumerate(encoder_classes)
         if label in {"ckd", "disease", "positive", "1"}),
        None,
    )
    ckd_probability = float(probas[ckd_index]) if ckd_index is not None else 0.0

    if predicted_label in {"ckd", "disease", "positive", "1"}:
        prediction_text = "CKD Risk Detected"
        risk = "High" if confidence >= 70 else "Medium"
        color = "danger" if confidence >= 70 else "warning"
    else:
        prediction_text = "Healthy"
        risk = "Low"
        color = "success"

    return {
        "prediction": prediction_text,
        "risk": risk,
        "confidence": f"{confidence:.1f}%",
        "probability": round(ckd_probability, 4),
        "color": color,
        "label": predicted_label,
        "disclaimer": "Academic screening estimate only; not a medical diagnosis.",
    }
