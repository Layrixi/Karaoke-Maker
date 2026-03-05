import demucs

#uses demucs for now, will create a custom model later on
class vocalRemovalModelHandler:
    def __init__(self):
        self.model = demucs.pretrained.get_model("demucs")

    
    def remove_vocals(self, audio_file):
        """Removes vocals from the given audio file and returns the instrumental version."""
        audio = demucs.audio.load(audio_file)
        stems = self.model.separate(audio)
        return stems["vocals"]
    
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()