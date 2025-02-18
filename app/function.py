from io import BytesIO
import numpy as np
import mne
import pickle
import os
import tempfile
import joblib

# Get the absolute path to the current directory (where function.py is)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to scaler.pkl
scaler_path = os.path.join(current_dir, "scaler.pkl")
scaler = joblib.load(scaler_path)

def preprocess_edf(file, scaler):
    """
    Preprocess EEG file: Load .edf, extract features, and segment into 10-second windows.
    This function also applies the same scaler used during training for preprocessing.
    """
    try:
        # Step 1: Create a temporary file to save the uploaded .edf file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".edf") as temp_file:
            temp_file.write(file.file.read())  # Write file contents to temp file
            temp_file.flush()  # Ensure data is written before reading
            temp_file_name = temp_file.name  # Store the temp file name for later use

        try:
            # Step 2: Load the EDF file using MNE
            raw = mne.io.read_raw_edf(temp_file_name, preload=True, verbose=False)
            data = raw.get_data()  # Shape (channels, time_samples)
            
            # Step 3: Extract features and segment the data into 10-second windows
            segment_length = 10 * int(raw.info['sfreq'])  # 10-second segment length
            num_segments = data.shape[1] // segment_length
            segments = []

            for i in range(num_segments):
                segment = data[:, i * segment_length: (i + 1) * segment_length]
                segments.append(segment)

            # Step 4: Convert to numpy array
            segments = np.array(segments)
            
            # Step 5: Reshape segments for CNN model - expected input shape (None, 32, 44, 1)
            # From your model summary, the first Conv2D layer expects input shape (None, 31, 43, 128)
            # We'll use 32x44 as our target shape for each segment
            
            # First, determine the number of channels and time points in each segment
            n_segments, n_channels, n_timepoints = segments.shape
            
            # Reshape segments to match expected input dimensions for Conv2D
            # Assuming time frequency transformation or channel selection is needed
            # We'll aim for 32x44x1 dimensions
            
            # Approach: If we have multiple channels, we can use a subset or average them
            if n_channels > 1:
                # Option 1: Average the channels
                segments = np.mean(segments, axis=1, keepdims=True)
            else:
                # Reshape to have channel as the last dimension
                segments = segments.reshape(n_segments, n_timepoints, 1)
            
            # Now scale each segment individually
            scaled_segments = np.zeros_like(segments)
            for i in range(segments.shape[0]):
                # Scale each time point (treating channel as feature)
                scaled_data = np.array([
                    scaler.transform(segments[i, :, c].reshape(-1, 1)).flatten()
                    for c in range(segments.shape[2])
                ]).T
                scaled_segments[i] = scaled_data.reshape(segments[i].shape)
            
            # Reshape to match the input dimensions of the first Conv2D layer
            target_height, target_width = 32, 44  # Based on expected input shape
            
            processed_segments = []
            for segment in scaled_segments:
                # Resize the segment to target dimensions
                if segment.shape[0] != target_height or segment.shape[1] != target_width:
                    # Use interpolation to resize
                    resized = np.zeros((target_height, target_width, 1))
                    for c in range(segment.shape[2]):
                        channel_data = segment[:, c].reshape(-1, 1)
                        # Resize to match expected input shape
                        if segment.shape[0] > target_height:
                            # Downsample by taking stride
                            stride = segment.shape[0] // target_height
                            resized_channel = channel_data[::stride, :][:target_height, :]
                        else:
                            # Upsample by repeating
                            repeats = int(np.ceil(target_height / segment.shape[0]))
                            resized_channel = np.repeat(channel_data, repeats, axis=0)[:target_height, :]
                        
                        # Reshape for width
                        if len(channel_data) > target_width:
                            stride = len(channel_data) // target_width
                            resized_channel = resized_channel[::stride][:target_width]
                        else:
                            repeats = int(np.ceil(target_width / len(channel_data)))
                            resized_channel = np.repeat(resized_channel, repeats, axis=0)[:target_width]
                        
                        resized[:, :, c] = resized_channel.reshape(target_height, target_width)
                    processed_segments.append(resized)
                else:
                    processed_segments.append(segment)
            
            return np.array(processed_segments)
        
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_name):
                os.unlink(temp_file_name)
    
    except Exception as e:
        print(f"Error in preprocess_edf: {e}")
        raise  # Reraise the error for further debugging

