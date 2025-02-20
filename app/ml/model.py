import numpy as np
import logging
from . import model 
from .preprocessing import process_for_prediction

logger = logging.getLogger(__name__)

def predict_api(file_path: str) -> dict:
    """
    Process EEG file and return prediction with detailed analysis
    """
    try:
        # Get preprocessed spectrograms
        spectrograms = process_for_prediction(file_path)
        logger.info(f"Processing file: {file_path}")
        logger.info(f"Input shape: {spectrograms.shape}")
        
        # Make predictions using the loaded model
        if model is None:
            raise ValueError("Model not properly initialized")
            
        raw_predictions = model.predict(spectrograms)
        logger.info(f"Made predictions successfully. Shape: {raw_predictions.shape}")
        
        # Process each segment's prediction
        detailed_segments = []
        healthy_count = 0
        mdd_count = 0
        
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
        
        # Determine final prediction
        final_prediction = "Healthy" if healthy_count >= mdd_count else "Major Depressive Disorder"
        total_segments = healthy_count + mdd_count
        majority_confidence = max(healthy_count, mdd_count) / total_segments * 100
        
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
                "spectrogram_shape": spectrograms.shape,
                "healthy_ratio": f"{healthy_count}/{total_segments}",
                "mdd_ratio": f"{mdd_count}/{total_segments}"
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }