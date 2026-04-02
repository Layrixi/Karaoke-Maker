import pathlib
import torch

VIDEO_LEN: float = 0.0

#check if cuda is available
def check_device():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return device

#returns path to the uploaded audio file
def get_audio_path(filename):
    return pathlib.Path(__file__).parent / "uploads" / "audio" / filename


def set_video_duration(seconds: float):
    global VIDEO_LEN
    VIDEO_LEN = seconds

def get_video_duration() -> float:
    return VIDEO_LEN