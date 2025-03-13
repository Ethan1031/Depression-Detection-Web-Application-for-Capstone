import mne
import numpy as np
from scipy import signal
import pickle
import os
import cv2  # Make sure OpenCV is installed and imported
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

def reject_criteria(x):
    """
    Criteria for rejecting noisy segments in EEG data.
    Rejects segments with amplitudes > 1e-4V or < -1e-4V.
    
    Args:
        x: EEG data segment
        
    Returns:
        tuple: (reject_flag, reasons)
    """
    max_condition = np.max(x, axis=1) > 1e-4
    min_condition = np.min(x, axis=1) < -1e-4
    
    return ((max_condition.any() or min_condition.any()), ["max amp", "min amp"])

def preprocess_eeg(file_path):
    """
    Preprocess EEG data according to the protocol in the notebook.
    
    Args:
        file_path: Path to the .edf file
        
    Returns:
        np.array: Preprocessed EEG data
    """
    try:
        # Read EEG file
        data = mne.io.read_raw_edf(file_path, preload=True)
        
        # Basic preprocessing
        data.set_eeg_reference()
        data.filter(l_freq=0.1, h_freq=70)
        data.notch_filter(50)
        
        # Drop specific channels based on total channels - exactly as in the notebook
        if data.info['nchan'] == 22:
            data.drop_channels(['EEG 23A-23R', 'EEG 24A-24R', 'EEG A2-A1', 'EEG C3-LE', 'EEG F4-LE'])
        elif data.info['nchan'] == 20:
            data.drop_channels(['EEG A2-A1', 'EEG C3-LE', 'EEG F4-LE'])
            
        # Rename channels to standard names as done in the notebook
        data.rename_channels({
            'EEG Fp1-LE': 'Fp1', 'EEG Fp2-LE': 'Fp2',
            'EEG F7-LE': 'F7', 'EEG F3-LE': 'F3', 'EEG Fz-LE': 'Fz', 'EEG F8-LE': 'F8',
            'EEG T3-LE': 'T3', 'EEG Cz-LE': 'Cz', 'EEG C4-LE': 'C4', 'EEG T4-LE': 'T4',
            'EEG T5-LE': 'T5', 'EEG P3-LE': 'P3', 'EEG Pz-LE': 'Pz', 'EEG P4-LE': 'P4', 'EEG T6-LE': 'T6',
            'EEG O1-LE': 'O1', 'EEG O2-LE': 'O2'
        })
        data.set_montage(mne.channels.make_standard_montage("standard_1020"))
        
        # Apply ICA - exactly as in the notebook
        ica = mne.preprocessing.ICA(random_state=42, n_components=13)
        ica.fit(data.copy().filter(l_freq=1.0, h_freq=None))
        data = ica.apply(data.copy())
        
        # Create 5-second epochs with 2-second overlap - matching the notebook's first code cell
        epochs = mne.make_fixed_length_epochs(data, duration=5, overlap=2)
        
        # Drop bad epochs based on amplitude criteria
        epochs.drop_bad(reject=dict(eeg=reject_criteria))
        
        # Get data array
        array = epochs.get_data()
        
        logger.info(f"Preprocessed EEG shape: {array.shape}")
        return array
        
    except Exception as e:
        logger.error(f"Error in EEG preprocessing: {str(e)}")
        raise

def process_for_prediction(file_path):
    """
    Complete preprocessing pipeline for model prediction.
    
    Args:
        file_path: Path to the .edf file
        
    Returns:
        np.array: Processed data ready for model prediction
    """
    try:
        # Get preprocessed data
        data_array = preprocess_eeg(file_path)
        
        # Apply z-score normalization (StandardScaler)
        original_shape = data_array.shape
        array_flattened = data_array.reshape(-1, 1)
        
        # Check if scaler exists, otherwise create new one
        current_dir = os.path.dirname(os.path.abspath(__file__))
        scaler_path = os.path.join(current_dir, "scaler.pkl")
            
        if os.path.exists(scaler_path):
            # Load existing scaler
            with open(scaler_path, "rb") as f:
                scaler = pickle.load(f)
                logger.info(f"Loaded scaler from {scaler_path}")
        else:
            # Create new scaler
            scaler = StandardScaler()
            scaler.fit(array_flattened)
            logger.info("Created new scaler")
            
            # Save the new scaler
            with open(scaler_path, "wb") as f:
                pickle.dump(scaler, f)
            logger.info(f"Saved new scaler to {scaler_path}")
        
        # Apply the scaling
        scaled_data = scaler.transform(array_flattened)
        data_array = scaled_data.reshape(original_shape)
        
        # Calculate mean across channels - exactly as in the notebook
        mean_signals = []
        for d in data_array:
            mean_signals.append(np.mean(d, axis=0))
        
        # Create spectrograms - exactly as in the notebook
        X_data = []
        
        for d in mean_signals:
            # Generate spectrogram using exact parameters from the notebook
            frequencies, times, stft_data = signal.spectrogram(
                x=d, 
                fs=256, 
                window=('tukey', 0.25), 
                nperseg=32, 
                noverlap=16, 
                nfft=32
            )
            
            # Process the spectrogram exactly as in the notebook
            resized_spectrogram = np.abs(stft_data)
            resized_spectrogram = resized_spectrogram / np.max(resized_spectrogram)
            
            # Resize to match dimensions used in the notebook (75, 17)
            resized_spectrogram = cv2.resize(resized_spectrogram, dsize=(75, 17), interpolation=cv2.INTER_CUBIC)
            
            # Split array into 3 parts as done in the notebook
            split_array = np.split(resized_spectrogram, 3, axis=1)
            spectrogram_array = np.array(split_array)
            
            X_data.append(spectrogram_array)
        
        X_data = np.array(X_data)
        logger.info(f"Final spectrograms shape: {X_data.shape}")
        
        return X_data
        
    except Exception as e:
        logger.error(f"Error in prediction processing: {str(e)}")
        raise

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python preprocessing.py <edf_file_path>")
        sys.exit(1)
    
    edf_file = sys.argv[1]
    
    # Process the file
    spectrograms = process_for_prediction(edf_file)
    print(f"Successfully processed file. Output shape: {spectrograms.shape}")