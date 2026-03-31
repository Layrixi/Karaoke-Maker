import subprocess
import pathlib
import tempfile
from dataclasses import dataclass, field
from typing import Optional
import shutil

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

    def __init__(self, ffmpeg_path: str = "ffmpeg", style: TextStyle | None = None):
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
        lines       : list of dicts with keys ``text`` (str) and
                      ``timestamp`` (float, seconds)
        output_path : where to save the rendered video (mp4)
        timeout     : ffmpeg subprocess timeout in seconds

        Returns
        -------
        pathlib.Path to the output file
        """

        _require_ffmpeg()

        video_path  = pathlib.Path(video_path)
        output_path = pathlib.Path(output_path)

        lines = [l for l in lines if l.get("timestamp") is not None]
        if not lines:
            raise ValueError("No lines with a timestamp provided.")

        srt_content = self._build_srt(lines)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".srt", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(srt_content)
            srt_path = pathlib.Path(tmp.name)

        try:
            self._run_ffmpeg(video_path, srt_path, output_path, timeout)
        finally:
            srt_path.unlink(missing_ok=True)

        return output_path

    # Private helpers
   
    def _escape(self, text: str) -> str:
        """Saves ffmpeg from breaking by misinterpreting special characters in the subtitle text."""
        return (
            text
            .replace("\\", "\\\\")
            .replace("'",  "\\'")
            .replace(":",  "\\:")
        )
    

    def _run(self, cmd: list[str], verbose: bool):
        if verbose:
            print("Running:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=not verbose, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")
    def _run_ffmpeg(
        self,
        video_path: pathlib.Path,
        srt_path: pathlib.Path,
        output_path: pathlib.Path,
        timeout: int,
    ):
        srt_ffmpeg = str(srt_path).replace("\\", "/").replace(":", "\\:")

        #to be changed later to not force the default
        ass_style = self._to_force_style()
        force_style = ",".join(f"{k}={v}" for k, v in ass_style.items())

        cmd = [
            self.ffmpeg_path, "-y",
            "-i", str(video_path),
            "-vf", f"subtitles='{srt_ffmpeg}':force_style='{force_style}'",
            "-c:a", "copy",
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            raise RuntimeError(
                f"FFmpeg exited with code {result.returncode}:\n{result.stderr[-1000:]}"
            )

    #to implement later
    @classmethod
    def _to_ass_color(cls, color: str):
        """Convert color like 'black@0.5' or '#RRGGBB' into ASS &HAABBGGRR."""
        token = color.strip().lower()
        opacity = 1.0
        if "@" in token:
            base, alpha_part = token.split("@", 1)
            token = base.strip()
            try:
                opacity = float(alpha_part)
            except ValueError:
                opacity = 1.0
        opacity = max(0.0, min(1.0, opacity))

        if token.startswith("#"):
            hex_code = token[1:]
        elif token.startswith("0x"):
            hex_code = token[2:]
        elif token in cls._NAMED_COLORS:
            r, g, b = cls._NAMED_COLORS[token]
            hex_code = f"{r:02x}{g:02x}{b:02x}"
        else:
            # Fallback to white if unknown input is provided.
            hex_code = "ffffff"

        if len(hex_code) != 6:
            hex_code = "ffffff"

        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        aa = int(round((1.0 - opacity) * 255))
        return f"&H{aa:02X}{b:02X}{g:02X}{r:02X}"

    def _ass_alignment(self):
        v = self.style.vertical_position.lower()
        h = self.style.horizontal_position.lower()

        row = {"bottom": 0, "center": 1, "top": 2}.get(v, 1)
        col = {"left": 0, "center": 1, "right": 2}.get(h, 1)

        table = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ]
        return table[row][col]

    def _to_force_style(self):
        style = self.style
        font_name = "Arial"
        if style.font_file:
            font_name = pathlib.Path(style.font_file).stem or "Arial"

        return {
            "Alignment": self._ass_alignment(),
            "Fontname": font_name,
            "Fontsize": style.font_size,
            "Bold": 0,
            "PrimaryColour": self._to_ass_color(style.font_color),
            "OutlineColour": self._to_ass_color(style.border_color),
            "Outline": max(0, style.border_width),
            "BorderStyle": 3 if style.box else 1,
            "BackColour": self._to_ass_color(style.box_color),
            "Shadow": max(abs(style.shadow_x), abs(style.shadow_y)) if style.shadow else 0,
            "Spacing": style.line_spacing,
        }

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
            f"text='{self._escape(text)}'",
            f"fontsize={style.font_size}",
            f"fontcolor={style.font_color}",
            f"x={x}",
            f"y={y}",
            f"line_spacing={style.line_spacing}",
        ]
    
        if style.font_file:
            parts.append(f"fontfile='{style.font_file}'")
    
        if style.box:
            parts += [
                f"box=1",
                f"boxcolor={style.box_color}",
                f"boxborderw={style.box_padding}",
            ]
    
        if style.shadow:
            parts += [
                f"shadowcolor={style.shadow_color}",
                f"shadowx={style.shadow_x}",
                f"shadowy={style.shadow_y}",
            ]
    
        if style.border_width > 0:
            parts += [
                f"borderw={style.border_width}",
                f"bordercolor={style.border_color}",
            ]
    
        # May generate a bug, if video is less than 99999 seconds and start time is not provided it may expand the video length    
        # to test later
        if start_time is not None:
            parts.append(f"enable='between(t,{start_time},{end_time or 99999})'")
    
        return "drawtext=" + ":".join(parts)
        
# testing main, to be removed later
if __name__ == "__main__":

    VIDEO_DIR  = pathlib.Path(__file__).parent.parent / "uploads" / "video"
    OUTPUT_DIR  = pathlib.Path(__file__).parent.parent / "uploads" / "output"
    vid = "karabin.mp4"
    video_path = VIDEO_DIR / vid


    LINES = [
        {"text": "Hello world",        "timestamp": 0.0},
        {"text": "TextBurner works",   "timestamp": 1.0},
        {"text": "Subtitles on video", "timestamp": 2.0},
        {"text": "Done",               "timestamp": 3.0},
    ]

    # --- Burn with default style ---
    out = OUTPUT_DIR / f"{video_path.stem}_burned.mp4"
    print(f"--- Burning subtitles → {out} ---")
    burner.burn(video_path, LINES, out)
    print("Done.")
