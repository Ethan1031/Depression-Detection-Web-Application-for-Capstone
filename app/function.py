import mne
import numpy as np
from scipy import signal
import pickle
import os

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
    """Create spectrogram of specific size (33x44)"""
    # Generate spectrogram
    frequencies, times, Sxx = signal.spectrogram(
        x=signal_data,
        fs=256,  # Sampling frequency
        window=signal.windows.tukey(64, 0.25),
        nperseg=64,
        noverlap=32,
        scaling='spectrum'
    )
    
    # Convert to dB scale and normalize
    Sxx = 10 * np.log10(Sxx + 1e-10)  # Add small constant to avoid log(0)
    Sxx = (Sxx - np.min(Sxx)) / (np.max(Sxx) - np.min(Sxx))
    
    # Resize to 33x44
    from scipy.ndimage import zoom
    zoom_factors = (33/Sxx.shape[0], 44/Sxx.shape[1])
    resized_spectrogram = zoom(Sxx, zoom_factors, order=1)
    
    return resized_spectrogram

def process_for_prediction(file_path):
    """Complete preprocessing pipeline for prediction"""
    # Load scaler
    scaler_path = os.path.join("app", "scaler.pkl")

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    
    # Get mean signals
    mean_signals = preprocess_eeg(file_path)
    
    # Scale the signals
    scaled_signals = []
    for signal_data in mean_signals:
        # Reshape for scaler
        reshaped_signal = signal_data.reshape(-1, 1)
        scaled = scaler.transform(reshaped_signal)
        scaled_signals.append(scaled.ravel())
    
    # Create spectrograms
    spectrograms = []
    for signal_data in scaled_signals:
        spec = create_spectrogram(signal_data)
        spectrograms.append(spec)
    
    # Stack and reshape for model input (batch_size, 33, 44, 1)
    spectrograms = np.stack(spectrograms)
    spectrograms = spectrograms.reshape((*spectrograms.shape, 1))
    
    return spectrograms
