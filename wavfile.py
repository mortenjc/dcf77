import wave

def read_file(file_path):
    with wave.open(file_path, 'rb') as wav_file:
        n_channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        frame_rate = wav_file.getframerate()
        n_frames = wav_file.getnframes()
        
        audio_data = wav_file.readframes(n_frames)
        
        return {
            'channels': n_channels,
            'sample_width': sample_width,
            'frame_rate': frame_rate,
            'n_frames': n_frames,
            'audio_data': audio_data
        }