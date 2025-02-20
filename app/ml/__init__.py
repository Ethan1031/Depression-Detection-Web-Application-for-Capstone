import os
import tensorflow as tf
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the model globally at module level
model = None

def initialize_model():
    global model
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "model.h5")
        logger.info(f"Loading model from: {model_path}")
        model = tf.keras.models.load_model(model_path)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise

# Initialize the model when module is imported
initialize_model()

from .model import predict_api
from .preprocessing import process_for_prediction

__all__ = ['predict_api', 'process_for_prediction']