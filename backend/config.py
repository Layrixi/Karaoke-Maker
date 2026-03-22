import pathlib
import torch




#check if cuda is available
def check_device():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    return device

#returns path to the uploaded audio file
def get_audio_path(filename):
    return pathlib.Path(__file__).parent / "uploads" / "audio" / filename

