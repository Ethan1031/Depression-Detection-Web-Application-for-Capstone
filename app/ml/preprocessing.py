import mne
import numpy as np
from scipy import signal
import pickle
import os
import logging

logger = logging.getLogger(__name__)

def preprocess_eeg(file_path):
    """Preprocess EEG data to get mean signal"""
    # Read EEG file
    raw = mne.io.read_raw_edf(file_path, preload=True)
    
    # Basic preprocessing
    raw.set_eeg_reference()
    raw.filter(l_freq=0.1, h_freq=70)
    raw.notch_filter(50)
    
    # Drop specific channels based on total channels
    if raw.info['nchan'] == 22:
        raw.drop_channels(['EEG 23A-23R', 'EEG 24A-24R', 'EEG Fz-LE', 'EEG Cz-LE', 'EEG Pz-LE'])
    elif raw.info['nchan'] == 20:
        raw.drop_channels(['EEG Fz-LE', 'EEG Cz-LE', 'EEG Pz-LE'])
    
    # Apply ICA
    ica = mne.preprocessing.ICA(random_state=42, n_components=13)
    ica.fit(raw.copy().filter(l_freq=1.0, h_freq=None))
    raw = ica.apply(raw)
    
    # Create 10-second epochs with 2-second overlap
    epochs = mne.make_fixed_length_epochs(raw, duration=10, overlap=2)
    
    # Get data array
    data = epochs.get_data()
    
    # Calculate mean across channels for each epoch
    mean_signals = np.mean(data, axis=1)  # Mean across channels
    
    return mean_signals

def create_spectrogram(signal_data):
    """Create spectrogram matching training parameters exactly"""
    try:
        # Generate spectrogram using exact training parameters
        frequencies, times, Sxx = signal.spectrogram(
            x=signal_data,
            fs=256,  # Sampling frequency
            window=signal.windows.tukey(64, 0.25),  # Match training parameters
            nperseg=64,
            noverlap=32
        )
        
        # Match the exact resize dimensions from training (33, 45)
        resized_spectrogram = np.abs(Sxx)
        
        # Normalize by max value as done in training
        resized_spectrogram = resized_spectrogram / np.max(resized_spectrogram)
        
        # Resize to match model input shape (33, 45)
        from scipy.ndimage import zoom
        zoom_factors = (33/resized_spectrogram.shape[0], 45/resized_spectrogram.shape[1])
        resized_spectrogram = zoom(resized_spectrogram, zoom_factors, order=1)
        
        return resized_spectrogram
        
    except Exception as e:
        logger.error(f"Error in spectrogram creation: {str(e)}")
        raise

def process_for_prediction(file_path):
    """Complete preprocessing pipeline matching training exactly"""
    try:
        # Load scaler
        current_dir = os.path.dirname(os.path.abspath(__file__))
        scaler_path = os.path.join(current_dir, "scaler.pkl")
        
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Scaler not found at {scaler_path}")
            
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)
        
        # Get preprocessed data
        mean_signals = preprocess_eeg(file_path)
        logger.info(f"Preprocessed signals shape: {mean_signals.shape}")
        
        # Scale the signals
        scaled_signals = []
        for signal_data in mean_signals:
            reshaped_signal = signal_data.reshape(-1, 1)
            scaled = scaler.transform(reshaped_signal)
            scaled_signals.append(scaled.ravel())
        
        # Create spectrograms
        spectrograms = []
        for signal_data in scaled_signals:
            spec = create_spectrogram(signal_data)
            spectrograms.append(spec)
        
        # Stack and reshape to match model input shape (batch_size, 33, 45, 1)
        spectrograms = np.stack(spectrograms)
        spectrograms = spectrograms.reshape((*spectrograms.shape, 1))
        
        logger.info(f"Final spectrograms shape: {spectrograms.shape}")
        logger.info(f"Spectrogram range: [{np.min(spectrograms):.4f}, {np.max(spectrograms):.4f}]")
        
        return spectrograms
        
    except Exception as e:
        logger.error(f"Error in prediction processing: {str(e)}")
        raise