import mne
import numpy as np
from scipy import signal
import pickle
import os
import cv2

def preprocess_eeg(file_path):
    """Preprocess EEG data to get mean signal"""
    # Read EEG file
    raw = mne.io.read_raw_edf(file_path, preload=True)
    
    # Basic preprocessing
    raw.set_eeg_reference()
    raw.filter(l_freq=0.1, h_freq=70)
    raw.notch_filter(50)
    
    # Channel handling needs to be updated to match notebook implementation
    if raw.info['nchan'] == 22:
        raw.drop_channels(['EEG 23A-23R', 'EEG 24A-24R', 'EEG A2-A1', 'EEG C3-LE', 'EEG F4-LE'])
    elif raw.info['nchan'] == 20:
        raw.drop_channels(['EEG A2-A1', 'EEG C3-LE', 'EEG F4-LE'])
    
    # Add channel renaming step from notebook
    raw.rename_channels({
        'EEG Fp1-LE': 'Fp1', 'EEG Fp2-LE': 'Fp2',
        'EEG F7-LE': 'F7', 'EEG F3-LE': 'F3', 'EEG Fz-LE': 'Fz', 'EEG F8-LE': 'F8',
        'EEG T3-LE': 'T3', 'EEG Cz-LE': 'Cz', 'EEG C4-LE': 'C4', 'EEG T4-LE': 'T4',
        'EEG T5-LE': 'T5', 'EEG P3-LE': 'P3', 'EEG Pz-LE': 'Pz', 'EEG P4-LE': 'P4', 'EEG T6-LE': 'T6',
        'EEG O1-LE': 'O1', 'EEG O2-LE': 'O2'
    })
    raw.set_montage(mne.channels.make_standard_montage("standard_1020"))
    
    # Apply ICA
    ica = mne.preprocessing.ICA(random_state=42, n_components=13)
    ica.fit(raw.copy().filter(l_freq=1.0, h_freq=None))
    raw = ica.apply(raw)
    
    # Add rejection criteria from notebook
    def reject_criteria(x):
        max_condition = np.max(x, axis=1) > 1e-4
        min_condition = np.min(x, axis=1) < -1e-4
        return ((max_condition.any() or min_condition.any()), ["max amp", "min amp"])
    
    # Create epochs with proper duration
    epochs = mne.make_fixed_length_epochs(raw, duration=5, overlap=2)  # Changed from 10 to 5 seconds
    
    # Apply rejection criteria
    epochs.drop_bad(reject=dict(eeg=reject_criteria))
    
    # Get data array
    data = epochs.get_data()
    
    # Calculate mean across channels for each epoch
    mean_signals = np.mean(data, axis=1)
    
    return mean_signals

def create_spectrogram(signal_data):
    """Create spectrogram features matching the notebook implementation"""
    # Generate spectrogram with parameters matching notebook
    frequencies, times, stft_data = signal.spectrogram(
        x=signal_data, 
        fs=256,
        window=('tukey', 0.25),
        nperseg=32,
        noverlap=16,
        nfft=32
    )
    
    # Process as in notebook
    resized_spectrogram = np.abs(stft_data)
    resized_spectrogram = resized_spectrogram / np.max(resized_spectrogram)
    
    # Use opencv for resizing as in notebook
    resized_spectrogram = cv2.resize(resized_spectrogram, dsize=(75, 17), interpolation=cv2.INTER_CUBIC)
    
    # Split array into 3 parts as in notebook
    split_array = np.split(resized_spectrogram, 3, axis=1)
    spectrogram_array = np.array(split_array)
    
    return spectrogram_array

def process_for_prediction(file_path):
    """Complete preprocessing pipeline for prediction with updated parameters"""
    # Load scaler
    scaler_path = os.path.join("app", "scaler.pkl")
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    
    # Get mean signals
    mean_signals = preprocess_eeg(file_path)
    
    # Scale the signals
    original_shape = mean_signals.shape
    reshaped_signals = mean_signals.reshape(-1, 1)
    scaled = scaler.transform(reshaped_signals)
    scaled_signals = scaled.reshape(original_shape)
    
    # Get mean of channels
    mean_of_scaled = np.mean(scaled_signals, axis=1)
    
    # Create spectrograms
    spectrograms = []
    for signal_data in mean_of_scaled:
        spec = create_spectrogram(signal_data)
        spectrograms.append(spec)
    
    # Stack for model input
    spectrograms = np.array(spectrograms)
    return spectrograms
