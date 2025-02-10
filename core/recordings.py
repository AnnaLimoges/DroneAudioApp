import numpy as np
from scipy.io import wavfile
from pathlib import Path
import matplotlib.pyplot as plt
import json
from datetime import datetime
import streamlit as st

def normalize_audio(data: tuple) -> tuple:
    """
    Normalize the audio data to the range [-1, 1] for each channel.

    Parameters:
    - data (tuple): A tuple of 1D arrays, each representing the audio time series of one channel.
    
    Returns:
    - tuple: A tuple of normalized audio data for each channel.
    """
    normalized_data = []
    
    for channel in data:
        # Check if the channel is a 1D array
        if isinstance(channel, np.ndarray) and channel.ndim == 1:
            # Normalize the channel independently
            if np.max(np.abs(channel)) != 0:
                normalized_channel = channel / np.max(np.abs(channel))
            else:
                normalized_channel = channel  # If all zeros, leave unchanged
            normalized_data.append(normalized_channel)
        else:
            raise ValueError("Each channel must be a 1D numpy array")
    
    return tuple(normalized_data)


def load_microphone_recordings(folder_path: str):
    """
    Load microphone recordings from WAV files in the specified folder.

    Parameters:
    - folder_path (str): Path to the folder containing the WAV files.
    
    Returns:
    - tuple: Sample rate and a tuple of channel data arrays for each microphone recording.
    """
    # Specify the folder path
    folder_path = Path(folder_path)
    
     # Initialize dictionary to store audio data
    mic_recordings = []
    
    # Iterate over each .wav file in the folder
    for file_path in folder_path.glob("*.wav"):
        if file_path.is_file():  # Ensure it's a file, not a directory
            # Read the audio file
            rate, data = wavfile.read(str(file_path))
            #data = (data - np.min(data)) / (np.max(data) - np.min(data)) * 2 - 1
            data = data/np.max(np.abs(data))
            mic_recordings.append(data)
    
    # Check size of recordings stored
    print(f"Number of recordings: {len(mic_recordings)}")
    # Return the sample rate and the tuple of channel data
    return mic_recordings, rate

def load_wav_file(file_path: str, t_start: float = None, t_end: float = None):
    """
    Load a WAV file and return audio data with optional time slicing.

    Args:
        file_path (str): Path to the WAV file.
        t_start (float, optional): Start time in seconds.
        t_end (float, optional): End time in seconds.

    Returns:
        tuple: (audio data, sample rate)

    Raises:
        ValueError: If the file is not found or invalid.
    """
    # Specify file path
    file_path = Path(file_path)

    # Load and Normalize channels
    if file_path.is_file():
        rate, data = wavfile.read(str(file_path))
        data = data / np.max(np.abs(data), axis=0)  # Normalize channels

        # Apply time slicing if specified
        if t_start is not None or t_end is not None:
            num_samples = len(data)
            duration = num_samples / rate

            # Convert time bounds to sample indices
            start_idx = int(rate * (t_start if t_start is not None else 0))
            end_idx = int(rate * (t_end if t_end is not None else duration))

            # Ensure bounds are valid
            start_idx = max(0, min(start_idx, num_samples))
            end_idx = max(0, min(end_idx, num_samples))

            data = data[start_idx:end_idx]

    else:
        raise ValueError("File not found")

    return data, rate


#Metadata saving functions

def save_metadata(file_path, microphone_data, metadata):
    # Add timestamp to metadata
    metadata["timestamp"] = datetime.now().isoformat()
    
    # Combine microphone data and metadata
    save_data = {
        "microphones": microphone_data,
        "metadata": metadata
    }
    
    with open(file_path, "w") as json_file:
        json.dump(save_data, json_file, indent=4)
    
    st.success("Microphone information saved to " + file_path)


def read_metadata(file_path):
    """
    Reads microphone data and metadata from a JSON file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        tuple: (metadata, microphone_data)
    """
    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)

        metadata = data.get("metadata", {})
        microphone_data = data.get("microphones", {})
        st.success("Microphone info loaded from " + file_path)
        return metadata, microphone_data

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON file: {e}")
        return None, None



