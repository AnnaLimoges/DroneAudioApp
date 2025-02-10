import streamlit as st
from core import MicrophoneCalibrator, load_microphone_recordings, load_wav_file, plot_all, save_metadata, read_metadata
from scipy.io import wavfile

# Sidebar menu
menu = st.sidebar.radio("Select an option", ["Home", "Record Audio", "Process Audio", "Calibrate Microphones", "Info"])

if menu == "Home":
    st.title("Welcome to the Audio Fingerprint Generation Program")
    st.write("This is the home page of the app. Use the sidebar to navigate.")

elif menu == "Record Audio":
    st.title("Record Audio")
    # Options to batch or live record
    tab1, tab2 = st.tabs(["Batch","Live"])

    with tab1:
        st.title("Record as Batch")
        st.text("Easily generate formatted metadata files for individual recordings on MixPre SD card as you record them.")

        #Metadata
        st.header("Recording Info")

        # Initialize the session state to track the number of microphone fields
        if "mic_count" not in st.session_state:
            st.session_state.mic_count = 1

        # Metadata input fields
        with st.expander("Enter Metadata"):
            location = st.text_input("Location")
            operator = st.text_input("Operator Name")
            drone_model = st.text_input("Drone Model")
            notes = st.text_area("Additional Notes")

        # Function to add a new microphone input
        def add_microphone():
            st.session_state.mic_count += 1

        # Button to add microphone inputs
        st.button("Add Microphone", on_click=add_microphone)

        # Collect microphone data
        mic_dict = {}
        for i in range(st.session_state.mic_count):
            mic_number = st.number_input(f"Channel {i + 1} Microphone Number", key=f"mic_{i}")
            
            # Location inputs for the microphone
            col1, col2, col3 = st.columns(3)
            x = col1.number_input(f"X Coordinate (Mic {i + 1})", key=f"x_{i}")
            y = col2.number_input(f"Y Coordinate (Mic {i + 1})", key=f"y_{i}")
            z = col3.number_input(f"Z Coordinate (Mic {i + 1})", key=f"z_{i}")
            
            mic_dict[f"channel_{i + 1}"] = {
                "mic_number": mic_number,
                "location": {"x": x, "y": y, "z": z}
            }

        # File info
        st.header("File Info")
        metadata_folder = st.text_input('Path to save metadata', value="data/metadata/")
        metadata_file = st.text_input('Recording Name')
        metadata_path = metadata_folder + metadata_file

        # Button to save microphone data
        if st.button("Save Microphone Info"):
            if all(mic["mic_number"] for mic in mic_dict.values()):  # Ensure valid mic numbers
                metadata = {
                    "location": location,
                    "operator": operator,
                    "drone_model": drone_model,
                    "notes": notes
                }
                save_metadata(metadata_path, mic_dict, metadata)
            else:
                st.error("Please enter a valid microphone number for all fields.")


    with tab2:
        st.title("Record Live")
        st.text("Record live data from USB connection. Note only two channels can be recorded at a time.")

elif menu == "Process Audio":
    st.title("Process Audio Files")
    st.header("File Info")
    # Input for file path
    file_path = st.text_input('Enter the file path containing WAV file:', value='data/rawRecordings/ThrottleUp_ThrottleDown.WAV')
    saveimg = st.checkbox('Save plot as image')

    # Conditionally show the calibration file input field if the checkbox is checked
    if saveimg:
        save_path = st.text_input("Enter the file path and name to save image", value='data/fingerprints/')

    calibrate = st.checkbox('Calibrate audio data', value=False)
    if calibrate:
        calibrationFile = st.text_input('Path to calibration file', value = 'data/calibrationData/calibration_data.json')
        # Initialize microphone dictionary
        if "mic_dict" not in st.session_state:
            st.session_state.mic_dict = {}
        # Options to batch or live record
        loadchoice = st.selectbox("Select One:",["Manual microphone info","Use metadata from file"])

        if loadchoice == "Manual microphone info":
            # Input for microphones
            st.header("Calibration Info")
            # Initialize the session state to track the number of microphone fields
            if "mic_count" not in st.session_state:
                st.session_state.mic_count = 1
            # Function to add a new microphone input
            def add_microphone():
                st.session_state.mic_count += 1

            # Button to add microphone inputs
            st.button("Add Microphone", on_click=add_microphone)

            # Collect microphone data
            for i in range(st.session_state.mic_count):
                mic_number = st.number_input(f"Channel {i + 1} Microphone Number", key=f"mic_{i}")
                
                st.session_state.mic_dict[f"channel_{i + 1}"] = {
                    "mic_number": mic_number,
                }
            

        elif loadchoice == "Use metadata from file":
            metadata_path = st.text_input("Enter the file path containing metadata file:", value='data/metadata/')
            load_metadata_now = st.button("Load")
            if load_metadata_now:
                metadata, loaded_mic_dict = read_metadata(metadata_path)
                st.session_state.mic_dict.update(loaded_mic_dict)
                print(st.session_state.mic_dict)

    # Optional flags and time range
    st.header("Timestamps and Channels")
    t_start = st.number_input('Start time of desired audio section (in seconds)', min_value=0, value=0)
    t_end = st.number_input('End time of desired audio section (in seconds)', min_value=3, value=7)
    channel = st.number_input('Enter Channel # to Plot (zero indexed)', min_value=0, value=3)

    # Button to process the data
    if st.button('Process Audio'):
        if not file_path:
            st.error('Please enter a valid file path')
        else:
            # Load audio data
            [mic_recordings, rate] = load_wav_file(file_path, t_start, t_end)

            if calibrate:
                # Initialize the calibrator
                calibrator = MicrophoneCalibrator(ref_mic_index=1)
                # Load calibration data
                calibrator.load_calibration(calibrationFile)
                # Calibrate Channels
                print(st.session_state.mic_dict)
                mic_recordings = calibrator.apply_calibration_file(mic_recordings, rate, st.session_state.mic_dict)

            # Display the shape of the mic recordings
            st.write(f"Microphone recordings shape: {mic_recordings.shape}")

            # Plot the recordings for the third microphone
            st.subheader("Fingerprint Plot")
            fig = plot_all(mic_recordings[:, channel], rate)
            st.pyplot(fig)  # Display the plot
            if saveimg:
                fig.savefig(save_path)

elif menu == "Calibrate Microphones":
    st.title("Calibrate Microphones")
    st.write("This program will save the callibration files in microphone number order. This is used to determine the correct calibration data to apply when processing. It expects inputs of a folder with recordings of microphone sweeps ordered by microphones number.")
    st.write("This only needs to be done once for every set of microphones. Reference microphone is always microphone 1.")

    # Sweep folder input
    sweepFolder = st.text_input('Path to folder containing frequency sweeps', value="data/rawRecordings/CHIRPS")
    # Save calibration data
    calibrationFile = st.text_input('Path and filename to save calibration data', value='data/calibrationData/')
    #Generate calibation file
    generateCalibration = st.button('Generate Calibration')
    if generateCalibration:
        # Import microphone recordings
        [mic_recordings, rate] = load_microphone_recordings(sweepFolder)

        # Initialize the calibrator
        calibrator = MicrophoneCalibrator(ref_mic_index=1)

        # Cross-correlate to allign and trim signals
        aligned_signals = calibrator.align_signals(mic_recordings[0], mic_recordings)

        # Analyze frequency response and save calibration
        calibrator.analyze_frequency_response(aligned_signals,rate)
        calibrator.save_calibration("data/calibrationData/calibrationFile")
    
elif menu == "Info":
    st.title("About This App")
    st.text("""
    This app records and processes audio files to generate audio fingerprints and metatada files for microphone 
            calibration and analysis. Recording is designed to work with a MixPre sound mixer. It allows you to select
            various options to process and analyze audio. Microphone numbers correspond to the green tape on each mic.
    """)
