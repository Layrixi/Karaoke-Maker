from demucs.pretrained import get_model
from demucs.apply import apply_model
from demucs.htdemucs import HTDemucs
from demucs.audio import load, save
import librosa
import pathlib
import torch

#uses demucs for now, will create a custom model later on
class vocalRemovalModelHandler:
    def __init__(self,device = "cpu"):
        self.model = HTDemucs()
        if device == "cuda" and torch.cuda.is_available():
            self.model = self.model.to("cuda")
        else:
            self.model = self.model.to("cpu")
        # todo: load pretrained model wieghts, tensor stuff and other thingies
    
    def remove_vocals(self, audio_file):
        """Removes vocals from the given audio file and returns the instrumental version."""
        audio = demucs.load(audio_file)
        stems = self.model.separate(audio)
        return stems["vocals"]
    
def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    removalHandler = vocalRemovalModelHandler(device=device)
    file = pathlib.Path("Hypatia.mp3")
    mix = librosa.load(file, sr=None)
    instrumental = removalHandler.remove_vocals(mix)
    librosa.output.write_wav("Hypatia_instrumental.wav", instrumental, sr=None)

if __name__ == "__main__":
    main()