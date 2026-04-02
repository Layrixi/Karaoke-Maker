import subprocess
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Optional
import shutil
sys.path.append(str(pathlib.Path(__file__).parent.parent))
from config import set_video_duration, get_video_duration

"""
Class responsible for applying the text to the video.
It's also responsible for the rendering process.
"""


def _require_ffmpeg():
    if shutil.which("ffmpeg") is None:
        raise EnvironmentError("ffmpeg is not installed or not found in PATH.")
    
@dataclass
class TextStyle:
    """
    All visual properties for a text overlay.
    font_file:
        Path to a .ttf / .otf file.  When omitted ffmpeg uses its built-in font.
    """
 
    # ── Typography
    font_file:    Optional[str] = None         
    font_size:    int           = 64
    font_color:   str           = "white"
 
    # ── Background box
    box:          bool          = True
    box_color:    str           = "black@0.7"
    box_padding:  int           = 10            
 
    # ── Drop shadow
    shadow:       bool          = False
    shadow_color: str           = "black@0.6"
    shadow_x:     int           = 3             
    shadow_y:     int           = 3             
 
    # ── Border
    border_width: int           = 0             
    border_color: str           = "black"
 
    # ── Vertical position
    vertical_position: str      = "center"
 
    # ── Horizontal position
    horizontal_position: str    = "center"
 
    # ── Spacing
    line_spacing: int           = 10            

@dataclass
class TextSegment:
    """One piece of text with its own timing and style."""
    text:       str
    start_time: float                       # seconds; use 0 for "always on"
    end_time:   float                       # seconds
    style:      TextStyle = field(default_factory=TextStyle)

class TextBurner:
    """Burns subtitle text onto a video using FFmpeg's subtitles filter."""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        Parameters
        ----------
        ffmpeg_path : path/name of the ffmpeg executable
        """
        self.ffmpeg_path = ffmpeg_path
        
    #API

    def burn(
        self,
        video_path: str | pathlib.Path,
        output_path: str | pathlib.Path,
        lines: list[TextSegment],
        video_codec: str = "libx264",
        audio_codec: str = "copy",
        quality: int = 23, 
        verbose: bool = False,
        timeout: int = 300,
    ):
        """
        Burn subtitles into video and write the result.

        Parameters
        ----------
        video_path  : input video file
        output_path : where to save the rendered video (mp4)
        lines       : list of TextSegment objects defining the text, timing, and style of each subtitle line
        video_codec : ffmpeg video codec to use (default: libx264)
        audio_codec : ffmpeg audio codec to use (default: copy)
        quality     : ffmpeg CRF quality level (lower is better quality, default: 23)
        verbose     : if True, print ffmpeg command and output; debug purposes
        timeout     : ffmpeg subprocess timeout in seconds

        Returns
        -------
        pathlib.Path to the output file
        """

        _require_ffmpeg()

        video_path  = pathlib.Path(video_path)
        output_path = pathlib.Path(output_path)

        if not lines:
            raise ValueError("No lines with a timestamp provided.")

        #prepare lines for ffmpeg
        #BUG if there's only 1 line
        filter_lines = ",".join(
            self._build_drawtext_filter(line.text, line.style, line.start_time, line.end_time)
            for line in lines
        )
        print("hello")
        try:
            self._run_ffmpeg([
                self.ffmpeg_path, '-y',
                '-i', str(video_path),
                '-vf', filter_lines,
                '-c:v', video_codec,
                '-crf', str(quality),
                '-c:a', audio_codec,
                str(output_path),
            ], verbose=True)
            print(f"Video saved to: {output_path}")
        except RuntimeError as e:
            return RuntimeError(f"Failed to burn subtitles: {e}")
            
        return output_path

    # Private helpers
   
    def _escape(self, text: str) -> str:
        """Saves ffmpeg from breaking by misinterpreting special characters in the subtitle text."""
        return (
            text
            .replace("\\", "\\\\")
            .replace("'",  "\\'")
            .replace(":",  "\\:")
            .replace(",",  "\\,")
        )
    

    def _run_ffmpeg(self, cmd: list[str], verbose: bool):
        if verbose:
            print("Running:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=not verbose, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")
    
   

    #to implement later,basically rgb hex etc. to ASS
    def _position_expr(self, dimension: str, text_dimension: str, position: str = "center") -> str:
        """
        Translate a named position into an ffmpeg expression. Returns either center
        dimension      : "w" (width) or "h" (height)
        text_dimension : "tw" or "th"
        position       : "center" or treats as a raw pixel value / expression
        """
        if position == "center":
            return f"({dimension} - {text_dimension})/2"
        else:
            # treat as a raw pixel value / expression
            return position
    def _build_drawtext_filter(self, text: str, style: TextStyle, start_time: Optional[float] = None,
                            end_time: Optional[float] = None) -> str:
        """Build a single drawtext filter fragment."""
    
        x = self._position_expr("w", "tw", style.horizontal_position)
        y = self._position_expr("h", "th", style.vertical_position)
    
        parts = [
            f"text={self._escape(text)}",
            f"fontsize='{style.font_size}'",
            f"fontcolor='{style.font_color}'",
            f"x='{x}'",
            f"y='{y}'",
            f"line_spacing='{style.line_spacing}'",
        ]
    
        if style.font_file:
            parts.append(f"fontfile='{style.font_file}'")
    
        if style.box:
            parts += [
                f"box='1'",
                f"boxcolor='{style.box_color}'",
                f"boxborderw='{style.box_padding}'",
            ]
    
        if style.shadow:
            parts += [
                f"shadowcolor='{style.shadow_color}'",
                f"shadowx='{style.shadow_x}'",
                f"shadowy='{style.shadow_y}'",
            ]
    
        if style.border_width > 0:
            parts += [
                f"borderw='{style.border_width}'",
                f"bordercolor='{style.border_color}'",
            ]
    
        # May generate a bug, if video is less than 99999 seconds and start time is not provided it may expand the video length    
        # to test later
        if start_time is not None:
            effective_end = end_time if end_time is not None else (get_video_duration() or 99999)
            parts.append(f"enable='between(t\\,{start_time}\\,{effective_end})'")
    
        return "drawtext=" + ":".join(parts)
        
# testing main, to be removed later
if __name__ == "__main__":

    VIDEO_DIR  = pathlib.Path(__file__).parent.parent / "uploads" / "video"
    OUTPUT_DIR  = pathlib.Path(__file__).parent.parent / "uploads" / "output"
    vid = "karabin.mp4"
    video_path = VIDEO_DIR / vid
    burner = TextBurner()

    #didnt define style, it will take default, in the final app it will be taken from the frontend, to be changed later
    LINES = [
        TextSegment(text="Hello world",        start_time=0.0, end_time=1.0),
        TextSegment(text="TextBurner works",   start_time=1.0, end_time=2.0),
        TextSegment(text="Subtitles on video", start_time=2.0, end_time=3.0),
        TextSegment(text="Done",               start_time=3.0, end_time=4.0),
    ]
    LINES2 = [
        TextSegment(text="Let's get a little bit dirty",            start_time=0.0, end_time=0.0,  style=TextStyle(font_file=None, font_size=64, font_color='white', box=True, box_color='black@0.7', box_padding=10, shadow=False, shadow_color='black@0.6', shadow_x=3, shadow_y=3, border_width=0, border_color='black', vertical_position='center', horizontal_position='center', line_spacing=10)),
        TextSegment(text='A little bit nasty, a little bit gross',  start_time=0.0, end_time=0.0,  style=TextStyle(font_file=None, font_size=64, font_color='white', box=True, box_color='black@0.7', box_padding=10, shadow=False, shadow_color='black@0.6', shadow_x=3, shadow_y=3, border_width=0, border_color='black', vertical_position='center', horizontal_position='center', line_spacing=10)),
        TextSegment(text="Come on, it's never too early",           start_time=0.0, end_time=None, style=TextStyle(font_file=None, font_size=64, font_color='white', box=True, box_color='black@0.7', box_padding=10, shadow=False, shadow_color='black@0.6', shadow_x=3, shadow_y=3, border_width=0, border_color='black', vertical_position='center', horizontal_position='center', line_spacing=10))
    ]

    out = OUTPUT_DIR / f"{video_path.stem}_burned.mp4"
    _probe_and_set_duration(video_path)
    video_duration = get_video_duration()
    print(f"Video duration: {video_duration} seconds")
    print(f"--- Burning subtitles → {out} ---")
    Segment = TextBurner()._build_drawtext_filter(LINES2[2].text, LINES2[2].style, LINES2[2].start_time, LINES2[2].end_time)
    print(Segment)
    try:
        out = burner.burn(video_path=video_path, output_path=out, lines=LINES2)
    except RuntimeError as e:
        print(e)
    

    print("Done")
