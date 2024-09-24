import mlflow
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_diabetes
from sklearn.ensemble import RandomForestRegressor
import joblib

# Set the experiment ID and tracking URI
mlflow.set_experiment(experiment_id="0")
mlflow.set_tracking_uri(uri="http://localhost:5000")

# Enable autologging
mlflow.autolog()

# Load the dataset
db = load_diabetes()
X_train, X_test, y_train, y_test = train_test_split(db.data, db.target)

# Create and train the model
rf = RandomForestRegressor(n_estimators=20, max_depth=6, max_features=3)
rf.fit(X_train, y_train)

# Use the model to make predictions on the test dataset
predictions = rf.predict(X_test)

# Log the model to MLflow
with mlflow.start_run() as run:
    # Log the model
    mlflow.sklearn.log_model(rf, "model")

    # Register the model in the MLflow Model Registry
    model_uri = f"runs:/{run.info.run_id}/model"
    mlflow.register_model(model_uri, "RandomForestDiabetesModel")

