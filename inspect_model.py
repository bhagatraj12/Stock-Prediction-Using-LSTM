import h5py
import json

MODEL_PATH = "backend/long_model_lstm.h5"

with h5py.File(MODEL_PATH, "r") as f:
    model_config = f.attrs.get("model_config")

config = json.loads(model_config)

print("MODEL ARCHITECTURE:\n")
for layer in config["config"]["layers"]:
    print(layer["class_name"], layer["config"].get("units", ""))