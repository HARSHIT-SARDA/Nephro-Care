from model_service import train_and_save_model


if __name__ == "__main__":

    print("=" * 50)
    print("NephroCare ML Model Training")
    print("=" * 50)

    try:

        artifact = train_and_save_model()

        accuracy = artifact.get("accuracy", 0)

        print()
        print(f"Accuracy: {accuracy * 100:.2f}%")
        print("Model artifact saved successfully.")
        print("Model path: model/model.pkl")
        print()
        print("Training completed successfully ✅")

    except Exception as e:

        print()
        print("Training failed ❌")
        print("Error:", e)