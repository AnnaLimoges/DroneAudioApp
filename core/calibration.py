import numpy as np
import scipy.signal as signal
import json
import os
from pathlib import Path
from scipy.io import wavfile
import matplotlib.pyplot as plt

class MicrophoneCalibrator:
    def __init__(self, ref_mic_index=0):
        self.ref_mic_index = ref_mic_index
        self.calibration_data = {}

    def align_signals(self, ref_signal, mic_signals):
        """
        Align microphone signals based on cross-correlation with the reference signal.

        Parameters:
        - ref_signal: The reference microphone signal (1D numpy array).
        - mic_signals: List of 1D numpy arrays containing other microphone signals.

        Returns:
        - List of aligned microphone signals, all with the same length as the reference signal.
        """
        aligned_signals = []

        # Ensure the reference signal is 1D
        if ref_signal.ndim > 1:
            ref_signal = ref_signal[:, 0]  # Use the first channel if stereo

        for mic_signal in mic_signals:
            # Ensure the microphone signal is 1D
            if mic_signal.ndim > 1:
                mic_signal = mic_signal[:, 0]  # Use the first channel if stereo

            # Cross-correlation to find the best alignment
            correlation = signal.correlate(mic_signal, ref_signal, mode='full')
            offset = np.argmax(correlation) - len(ref_signal)  # Compute the offset

            # Align signal by shifting and trimming
            if offset > 0:
                aligned_signal = mic_signal[offset:]
            else:
                aligned_signal = np.pad(mic_signal, (abs(offset), 0), mode='constant')

            # Trim or pad to match the length of the reference signal
            aligned_signal = aligned_signal[:len(ref_signal)]
            aligned_signal = np.pad(aligned_signal, (0, len(ref_signal) - len(aligned_signal)), mode='constant')
            aligned_signals.append(aligned_signal)

        return aligned_signals
    
    def analyze_frequency_response(self, mic_recordings, sample_rate):
        """
        Analyze the frequency response of each microphone compared to the reference microphone.

        Parameters:
        - sweep_signal: The original frequency sweep signal.
        - mic_recordings: A list of arrays containing recordings from each microphone.
        - sample_rate: Sampling rate of the recordings.
        """
        # Compute FFT of the reference microphone's response
        ref_response = mic_recordings[self.ref_mic_index]
        ref_fft = np.abs(np.fft.rfft(ref_response))

        calibration_factors = []

        for i, mic_response in enumerate(mic_recordings):
            mic_fft = np.abs(np.fft.rfft(mic_response, n=len(ref_response)))

            # Calculate calibration factor as ratio of reference to microphone FFT
            cal_factor = ref_fft / mic_fft
            calibration_factors.append(cal_factor)

        # Save frequency bins for applying the calibration later
        frequency_bins = np.fft.rfftfreq(len(ref_response), 1 / sample_rate)
        self.calibration_data = {
            "frequency_bins": frequency_bins.tolist(),
            "calibration_factors": [cf.tolist() for cf in calibration_factors]
        }

    def save_calibration(self, filepath):
        """Save the calibration data to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.calibration_data, f)
            
    def load_calibration(self, filepath):
        """Load calibration data from a JSON file."""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                self.calibration_data = json.load(f)
        else:
            raise FileNotFoundError(f"Calibration file not found: {filepath}")

    def apply_calibration_folder(self, mic_recordings, sample_rate):
        """
        Apply calibration to new recordings where each chanel is its own file.

        Parameters:
        - mic_recordings: A list of arrays containing recordings from each microphone.
        - sample_rate: Sampling rate of the recordings.

        Returns:
        - A list of calibrated microphone recordings.
        """
        if not self.calibration_data:
            raise ValueError("Calibration data is not loaded.")

        frequency_bins = np.array(self.calibration_data["frequency_bins"])
        calibrated_recordings = []

        for i, mic_response in enumerate(mic_recordings):
            mic_fft = np.fft.rfft(mic_response, n=len(frequency_bins) * 2 - 1)
            calibration_factor = np.array(self.calibration_data["calibration_factors"][i])

            # Ensure the calibration factor length matches the mic FFT
            calibration_factor = np.resize(calibration_factor, mic_fft.shape)
            calibrated_fft = mic_fft * calibration_factor

            # Reconstruct the time-domain signal
            calibrated_response = np.fft.irfft(calibrated_fft, n=len(mic_response))
            calibrated_recordings.append(calibrated_response)

        return calibrated_recordings
    


    def apply_calibration_file(self, mic_recordings, sample_rate, mic_dict):
        """
        Apply calibration to new recordings.

        Parameters:
        - mic_recordings: A list of arrays or a 2D array containing recordings from each microphone.
        - sample_rate: Sampling rate of the recordings.
        - mic_dict: A dictionary containing microphone metadata in the format:
            {
                "channel_1": {
                    "mic_number": 1.0,
                    "location": {"x": 0.0, "y": 0.0, "z": 0.0}
                },
                "channel_2": {
                    "mic_number": 2.0,
                    "location": {"x": 0.0, "y": 0.0, "z": 0.0}
                }
            }

        Returns:
        - An array of calibrated microphone recordings with dimensions (channel, sample).
        """
        if not self.calibration_data:
            raise ValueError("Calibration data is not loaded.")

        # Ensure mic_dict is properly formatted
        if not isinstance(mic_dict, dict):
            raise ValueError("Invalid microphone dictionary format. Expected a dictionary of channel data.")

        mic_channels = list(mic_dict.keys())
        num_channels = len(mic_channels)

        # Check dimensionality consistency between mic_recordings and mic_dict
        if isinstance(mic_recordings, list):
            raise Warning("Audio input is in list form. You may want to use 'apply_calibration_folder'")
        elif isinstance(mic_recordings, np.ndarray) and mic_recordings.ndim == 2:
            if mic_recordings.shape[1] != num_channels:
                raise ValueError("Mismatch between the number of channels in mic_recordings and mic_dict.")
        else:
            raise ValueError("mic_recordings should be a list or 2D numpy array.")

        frequency_bins = np.array(self.calibration_data["frequency_bins"])
        calibrated_recordings = []

        for idx, channel_name in enumerate(mic_channels):
            mic_info = mic_dict.get(channel_name)
            if not mic_info or "mic_number" not in mic_info:
                raise ValueError(f"Missing microphone number for {channel_name}.")

            mic_number = int(mic_info["mic_number"]) - 1  # Assuming mic_number is used for calibration lookup

            # Handle case where channel order does not match mic number
            if mic_number < 0 or mic_number >= len(self.calibration_data["calibration_factors"]):
                raise ValueError(f"Invalid or out-of-range microphone number: {mic_number + 1}.")

            mic_response = mic_recordings[idx] if isinstance(mic_recordings, list) else mic_recordings[:, idx]

            mic_fft = np.fft.rfft(mic_response, n=len(frequency_bins) * 2 - 1)
            calibration_factor = np.array(self.calibration_data["calibration_factors"][mic_number])

            # Ensure the calibration factor length matches the mic FFT
            calibration_factor = np.resize(calibration_factor, mic_fft.shape)
            calibrated_fft = mic_fft * calibration_factor

            # Reconstruct the time-domain signal
            calibrated_response = np.fft.irfft(calibrated_fft, n=len(mic_response))
            calibrated_recordings.append(calibrated_response)

        if isinstance(mic_recordings, np.ndarray):
            calibrated_recordings = np.array(calibrated_recordings)
            calibrated_recordings = np.transpose(calibrated_recordings)

        return calibrated_recordings

