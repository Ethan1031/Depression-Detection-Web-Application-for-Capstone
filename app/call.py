from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse
import tensorflow as tf
import numpy as np
from .function import process_for_prediction
import os

current_dir = os.path.dirname(os.path.abspath(__file__))  
model_path = os.path.join(current_dir, "model.h5")

# Load the trained model
model = tf.keras.models.load_model(model_path)

# pythonCopymodel = tf.keras.models.load_model(model_path)
# print(model.summary())

router = APIRouter()

def predict_api(file_path: str) -> dict:
    """
    Process EEG file and return prediction
    
    Args:
        file_path (str): Path to the EEG file (.edf)
    
    Returns:
        dict: Prediction results including class and confidence
    """
    try:
        # Process the EEG file into spectrograms
        spectrograms = process_for_prediction(file_path)
        
        # Ensure spectrograms have correct shape
        if spectrograms.shape[1:] != (33, 44, 1):
            raise ValueError(f"Invalid spectrogram shape: {spectrograms.shape}. Expected (N, 33, 44, 1)")
        
        # Make predictions
        predictions = model.predict(spectrograms)
        
        # Average predictions across all segments
        avg_prediction = np.mean(predictions, axis=0)
        
        # Get class and confidence
        predicted_class = np.argmax(avg_prediction)
        confidence = float(avg_prediction[predicted_class])
        
        # Create response
        result = {
            "status": "success",
            "prediction": "Healthy" if predicted_class == 0 else "Major Depressive Disorder",
            "confidence": round(confidence * 100, 2),
            "segments_analyzed": len(spectrograms)
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }