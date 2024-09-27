import mlflow
from mlflow.models import infer_signature
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_diabetes
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score
from sklearn.metrics import log_loss

# Set the experiment ID and tracking URI
mlflow.set_experiment(experiment_id="0")
mlflow.set_tracking_uri(uri="http://localhost:5000")

# Enable autologging
mlflow.autolog()

# Load the dataset
db = load_diabetes()
X_train, X_test, y_train, y_test = train_test_split(db.data, db.target)
params = {"n_estimators":40, "max_depth":10, "max_features":4}

# Create and train the model
rf = RandomForestRegressor(**params)
rf.fit(X_train, y_train)

# Use the model to make predictions on the test dataset
predictions = rf.predict(X_test)
loss = log_loss(y_test, predictions)
# accuracy = accuracy_score(y_test, predictions)

# Log the model to MLflow
with mlflow.start_run() as run:
    mlflow.log_params(params)
    mlflow.log_metric("loss", loss)

    signature = infer_signature(X_train, rf.predict(X_train))
    model_info = mlflow.sklearn.log_model(
        skmodel=rf,
        artifact_path="diabetes_model",
        signature=signature,
        input_example=X_train,
        registered_model_name="do-you-diabetes-let-see"
    )

    model_uri = f"runs:/{run.info.run_id}/model"
    mlflow.register_model(model_uri, "RandomForestDiabetesModel")

