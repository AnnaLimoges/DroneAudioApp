from core import MicrophoneCalibrator, load_microphone_recordings, load_wav_file, plot_all
import argparse
from scipy.io import wavfile

# Create the parser
parser = argparse.ArgumentParser(description="Audio Fingerprint Generation Program")

# Add arguments
parser.add_argument('folder_path', type=str, help="Path to the folder containing the WAV files")

parser.add_argument('mics', nargs='+', type=int, help='List of microphones used in recordings')

# Optional flag with a default value (False if not specified)
parser.add_argument('--calibrate', action='store_true', help="Flag to calibrate audio data (default is False)")

parser.add_argument('--t_start', type=int, help='Start time of desired audio section')

parser.add_argument('--t_end', type=int, help='End time of desred audio section')
# Parse the arguments
args = parser.parse_args()

# Access the parsed arguments and their defaults if not provided
folder_path = args.folder_path
print(folder_path)
mics = args.mics
calibrate = args.calibrate
t_start = args.t_start if 't_start' in args else None
t_end = args.t_end if 't_end' in args else None

[mic_recordings, rate] = load_wav_file(folder_path,t_start,t_end)

if calibrate:
    # Initialize the calibrator
    calibrator = MicrophoneCalibrator(ref_mic_index=1)

    # Load callibration data
    calibrator.load_calibration('data/calibrationData/calibration_data.json')

    # Callibrate Channels
    mic_recordings = calibrator.apply_calibration_file(mic_recordings, rate, mics)

    # Save calibrated data
    #wavfile.write("stereo_output.wav", rate, mic_recordings)

print(mic_recordings.shape)
plot_all(mic_recordings[:,2], rate)






