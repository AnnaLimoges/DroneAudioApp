from core import MicrophoneCalibrator
from core import load_microphone_recordings, normalize_audio
import argparse

# Create the parser
parser = argparse.ArgumentParser(description="Microphone Data Analysis Program")

# Add arguments
# Example of positional argument (required)
parser.add_argument('--folder_path', type=str, default='data/rawRecordings/CHIRPS', help="Path to the folder containing the WAV files")

# Parse the arguments
args = parser.parse_args()

# Access the parsed arguments and their defaults if not provided
folder_path = args.folder_path

# Import microphone recordings
[mic_recordings, rate] = load_microphone_recordings(folder_path)

# Initialize the calibrator
calibrator = MicrophoneCalibrator(ref_mic_index=1)

# Cross-correlate to allign and trim signals
aligned_signals = calibrator.align_signals(mic_recordings[0], mic_recordings)

# Analyze frequency response and save calibration
calibrator.analyze_frequency_response(aligned_signals,rate)
calibrator.save_calibration("data/calibrationData/calibration_data.json")
