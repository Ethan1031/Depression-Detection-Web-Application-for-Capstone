from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse
import tensorflow as tf
import numpy as np
from app.function import preprocess_edf, scaler
import os
import traceback

current_dir = os.path.dirname(os.path.abspath(__file__))  
model_path = os.path.join(current_dir, "model.h5")

# Load the trained model
model = tf.keras.models.load_model(model_path)

pythonCopymodel = tf.keras.models.load_model(model_path)
print(model.summary())

router = APIRouter()

@router.post("/predict")
async def predict_api(file: UploadFile):
    try:
        # Preprocess the uploaded EEG file
        segments = preprocess_edf(file, scaler)

        # Check if preprocessing resulted in valid segments
        if segments.shape[0] == 0:
            raise ValueError("No valid EEG segments extracted from the file.")

        # Predict for each segment
        all_predictions = []
        
        # Process in batches if needed
        for i in range(0, segments.shape[0], 32):  # Using batch size of 32
            batch = segments[i:i+32]
            
            # If the last batch is smaller, pad it to match expected batch size
            if batch.shape[0] < 32:
                padding_shape = list(batch.shape)
                padding_shape[0] = 32 - batch.shape[0]  # Calculate padding needed
                padding = np.zeros(padding_shape)  # Create zero padding
                padded_batch = np.concatenate([batch, padding], axis=0)
                
                # Get predictions
                batch_preds = model.predict(padded_batch)
                
                # Only keep predictions for actual data (not padding)
                valid_count = batch.shape[0]
                batch_preds = batch_preds[:valid_count]
            else:
                # No padding needed
                batch_preds = model.predict(batch)
            
            all_predictions.extend(batch_preds.tolist())
        
        # Convert to numpy array
        all_predictions = np.array(all_predictions)
        
        # For binary classification - convert to labels (assuming sigmoid output)
        predicted_labels = (all_predictions > 0.5).astype(int)
        
        # If the output has two classes (shape[-1] == 2), take argmax
        if len(all_predictions.shape) > 1 and all_predictions.shape[-1] == 2:
            predicted_labels = np.argmax(all_predictions, axis=1)
        
        # Determine final result based on majority vote
        # Assuming class 1 is "Depressed" and class 0 is "Healthy"
        depression_count = np.sum(predicted_labels)
        final_prediction = "Depressed" if depression_count > len(predicted_labels) / 2 else "Healthy"

        return JSONResponse(content={"prediction": final_prediction})

    except Exception as e:
        error_message = str(e)
        traceback_str = traceback.format_exc()  # Get full error traceback
        print(f"Error: {error_message}\nTraceback:\n{traceback_str}")  # Print to console for debugging
        return JSONResponse(content={"error": error_message, "traceback": traceback_str}, status_code=500)
