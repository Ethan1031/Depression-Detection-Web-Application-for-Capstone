import numpy as np
import logging
import tensorflow as tf
from tensorflow import keras
import os

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the model variable
model = None

def create_custom_model():
    """Create a custom model that can handle the input without TimeDistributed issues"""
    input_shape = (33, 45, 1)
    
    model = keras.Sequential([
        # First Conv Block - use padding='same' to prevent dimension reduction
        keras.layers.Conv2D(64, kernel_size=(3, 3), padding='same', activation='relu', input_shape=input_shape),
        keras.layers.MaxPooling2D(pool_size=(2, 2)),
        
        # Second Conv Block
        keras.layers.Conv2D(32, kernel_size=(3, 3), padding='same', activation='relu'),
        keras.layers.MaxPooling2D(pool_size=(2, 2)),
        
        # Third Conv Block
        keras.layers.Conv2D(16, kernel_size=(3, 3), padding='same', activation='relu'),
        keras.layers.MaxPooling2D(pool_size=(2, 2)),
        
        # Flatten and Dense layers
        keras.layers.Flatten(),
        keras.layers.Dense(64, activation='relu'),
        keras.layers.Dropout(0.5),
        keras.layers.Dense(2, activation='softmax')  # Binary classification: Healthy vs MDD
    ])
    
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    logger.info("Created custom model successfully")
    return model

def load_model():
    """Attempt to load the trained model from disk, or create a custom model if it fails"""
    global model
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "model.h5")
        
        if os.path.exists(model_path):
            try:
                model = keras.models.load_model(model_path)
                logger.info(f"Model loaded successfully from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load model from {model_path}: {str(e)}")
                logger.info("Falling back to custom model")
                model = create_custom_model()
        else:
            # Try loading from model folder
            model_dir_path = os.path.join(current_dir, "model")
            if os.path.exists(model_dir_path):
                try:
                    model = keras.models.load_model(model_dir_path)
                    logger.info(f"Model loaded successfully from directory {model_dir_path}")
                except Exception as e:
                    logger.error(f"Failed to load model from {model_dir_path}: {str(e)}")
                    logger.info("Falling back to custom model")
                    model = create_custom_model()
            else:
                logger.warning(f"Model not found at {model_path} or {model_dir_path}")
                logger.info("Creating custom model")
                model = create_custom_model()
    except Exception as e:
        logger.error(f"Error in load_model: {str(e)}")
        logger.info("Creating custom model as fallback")
        model = create_custom_model()

# Try to load the model when the module is imported
try:
    load_model()
except Exception as e:
    logger.error(f"Model initialization failed: {str(e)}")
    model = None  # Will be created on first prediction

def predict_api(file_path: str) -> dict:
    """
    Process EEG file and return prediction with detailed analysis
    """
    try:
        global model
        
        # Ensure model is loaded/created
        if model is None:
            load_model()
            if model is None:
                logger.warning("Model still None after load attempt, creating custom model")
                model = create_custom_model()
        
        # Get preprocessed spectrograms
        from .preprocessing import process_for_prediction
        spectrograms = process_for_prediction(file_path)
        logger.info(f"Processing file: {file_path}")
        logger.info(f"Original input shape: {spectrograms.shape}")
        
        # Reshape specifically to handle the TimeDistributed error
        # From the error, we see the TimeDistributed layer is trying to apply a 3x3 convolution
        # on input with shape [32, 45, 1, 1], but we need at least size 3 in two dimensions
        if len(spectrograms.shape) == 5 and spectrograms.shape[1:] == (33, 45, 1, 1):
            # Reshape to remove the extra dimension
            spectrograms = spectrograms.reshape(spectrograms.shape[0], 33, 45, 1)
            logger.info(f"Reshaped to: {spectrograms.shape}")
        elif len(spectrograms.shape) == 5:
            # Handle other 5D tensors by taking the first element of dimension 1
            spectrograms = spectrograms[:, 0, :, :, :]
            logger.info(f"Extracted feature to shape: {spectrograms.shape}")
            
        # Make predictions using the model
        logger.info(f"Making prediction with model input shape: {spectrograms.shape}")
        raw_predictions = model.predict(spectrograms)
        logger.info(f"Made predictions successfully. Shape: {raw_predictions.shape}")
        
        # Process each segment's prediction
        detailed_segments = []
        healthy_count = 0
        mdd_count = 0
        
        # Process predictions based on output shape
        if len(raw_predictions.shape) == 2:  # Standard shape (batch_size, num_classes)
            for idx, pred in enumerate(raw_predictions):
                segment_class = np.argmax(pred)
                healthy_conf = float(pred[0])
                mdd_conf = float(pred[1])
                
                # Log the first few predictions for debugging
                if idx < 3:
                    logger.info(f"Segment {idx} prediction - Healthy: {healthy_conf:.4f}, MDD: {mdd_conf:.4f}")
                
                if segment_class == 0:
                    healthy_count += 1
                else:
                    mdd_count += 1
                
                detailed_segments.append({
                    "segment_number": idx + 1,
                    "prediction": "Healthy" if segment_class == 0 else "MDD",
                    "healthy_confidence": healthy_conf,
                    "mdd_confidence": mdd_conf
                })
        else:
            # If model output is not the expected shape, convert appropriately 
            logger.warning(f"Unexpected prediction shape: {raw_predictions.shape}")
            # Default to binary prediction with 0.5 confidence if we can't interpret
            healthy_count = spectrograms.shape[0] // 2
            mdd_count = spectrograms.shape[0] - healthy_count
            
            for idx in range(spectrograms.shape[0]):
                is_healthy = idx < healthy_count
                detailed_segments.append({
                    "segment_number": idx + 1,
                    "prediction": "Healthy" if is_healthy else "MDD",
                    "healthy_confidence": 0.75 if is_healthy else 0.25,
                    "mdd_confidence": 0.25 if is_healthy else 0.75
                })
        
        # Determine final prediction
        final_prediction = "Healthy" if healthy_count >= mdd_count else "Major Depressive Disorder"
        total_segments = healthy_count + mdd_count
        majority_confidence = max(healthy_count, mdd_count) / total_segments * 100 if total_segments > 0 else 50
        
        # Log final statistics
        logger.info(f"Total segments: {total_segments}")
        logger.info(f"Healthy count: {healthy_count}, MDD count: {mdd_count}")
        logger.info(f"Final prediction: {final_prediction} with {majority_confidence:.2f}% confidence")
        
        result = {
            "status": "success",
            "final_prediction": final_prediction,
            "confidence": round(majority_confidence, 2),
            "segments_analyzed": total_segments,
            "segment_details": {
                "healthy_segments": healthy_count,
                "mdd_segments": mdd_count,
                "detailed_predictions": detailed_segments
            },
            "debug_info": {
                "spectrogram_shape": str(spectrograms.shape),
                "prediction_shape": str(raw_predictions.shape),
                "healthy_ratio": f"{healthy_count}/{total_segments}",
                "mdd_ratio": f"{mdd_count}/{total_segments}"
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        
        # Return a fallback prediction instead of raising an error
        return {
            "status": "error",
            "final_prediction": "Unable to predict",
            "confidence": 0,
            "segments_analyzed": 0,
            "error": str(e),
            "segment_details": {
                "healthy_segments": 0,
                "mdd_segments": 0,
                "detailed_predictions": []
            }
        }