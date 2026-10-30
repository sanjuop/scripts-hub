import csv
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


# ============================================================
# SETTINGS
# ============================================================

CRF = 28
PRESET = "medium"
AUDIO_BITRATE = "96k"

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".mov",
    ".avi",
    ".m4v",
    ".webm",
}


# ============================================================
# FFPROBE
# ============================================================

def get_video_info(file_path):

    command = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    data = json.loads(result.stdout)

    video_stream = next(
        (
            stream
            for stream in data.get("streams", [])
            if stream.get("codec_type") == "video"
        ),
        None,
    )

    audio_stream = next(
        (
            stream
            for stream in data.get("streams", [])
            if stream.get("codec_type") == "audio"
        ),
        None,
    )

    if not video_stream:
        raise RuntimeError("No video stream found.")

    return {
        # ----------------------------------------------------
        # FORMAT
        # ----------------------------------------------------

        "container": data.get(
            "format", {}
        ).get(
            "format_name", ""
        ),

        "format_long_name": data.get(
            "format", {}
        ).get(
            "format_long_name", ""
        ),

        # ----------------------------------------------------
        # VIDEO
        # ----------------------------------------------------

        "width": video_stream.get(
            "width", ""
        ),

        "height": video_stream.get(
            "height", ""
        ),

        "video_codec": video_stream.get(
            "codec_name", ""
        ),

        "video_codec_long": video_stream.get(
            "codec_long_name", ""
        ),

        "video_profile": video_stream.get(
            "profile", ""
        ),

        "pixel_format": video_stream.get(
            "pix_fmt", ""
        ),

        "fps": video_stream.get(
            "r_frame_rate", ""
        ),

        "video_bitrate": video_stream.get(
            "bit_rate", ""
        ),

        "video_frames": video_stream.get(
            "nb_frames", ""
        ),

        "level": video_stream.get(
            "level", ""
        ),

        # ----------------------------------------------------
        # COLOR
        # ----------------------------------------------------

        "color_space": video_stream.get(
            "color_space", ""
        ),

        "color_transfer": video_stream.get(
            "color_transfer", ""
        ),

        "color_primaries": video_stream.get(
            "color_primaries", ""
        ),

        "color_range": video_stream.get(
            "color_range", ""
        ),

        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        "audio_codec": (
            audio_stream.get(
                "codec_name",
                "",
            )
            if audio_stream
            else ""
        ),

        "audio_codec_long": (
            audio_stream.get(
                "codec_long_name",
                "",
            )
            if audio_stream
            else ""
        ),

        "audio_bitrate": (
            audio_stream.get(
                "bit_rate",
                "",
            )
            if audio_stream
            else ""
        ),

        "audio_sample_rate": (
            audio_stream.get(
                "sample_rate",
                "",
            )
            if audio_stream
            else ""
        ),

        "audio_channels": (
            audio_stream.get(
                "channels",
                "",
            )
            if audio_stream
            else ""
        ),

        "audio_channel_layout": (
            audio_stream.get(
                "channel_layout",
                "",
            )
            if audio_stream
            else ""
        ),

        # ----------------------------------------------------
        # DURATION
        # ----------------------------------------------------

        "duration": float(
            data.get(
                "format",
                {},
            ).get(
                "duration",
                0,
            )
        ),
    }


# ============================================================
# FORMATTING FUNCTIONS
# ============================================================

def format_duration(seconds):

    seconds = int(seconds)

    hours = seconds // 3600

    minutes = (
        seconds % 3600
    ) // 60

    secs = seconds % 60

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d}"
    )


def format_size(size_bytes):

    if size_bytes >= 1024 ** 3:

        return (
            f"{size_bytes / (1024 ** 3):.2f}"
            " GB"
        )

    return (
        f"{size_bytes / (1024 ** 2):.1f}"
        " MB"
    )


def format_bitrate(value):

    if not value:
        return ""

    try:

        return round(
            float(value) / 1000,
            1,
        )

    except Exception:

        return ""


def format_fps(value):

    if not value:
        return ""

    try:

        numerator, denominator = (
            value.split("/")
        )

        fps = (
            float(numerator)
            /
            float(denominator)
        )

        return round(
            fps,
            3,
        )

    except Exception:

        return value


def format_time(seconds):

    seconds = int(seconds)

    hours = seconds // 3600

    minutes = (
        seconds % 3600
    ) // 60

    secs = seconds % 60

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d}"
    )


# ============================================================
# COMPRESS VIDEO
# ============================================================

def compress_video(
    input_file,
    output_file,
    convert_4k_to_1080p,
):

    info = get_video_info(
        input_file
    )

    width = info["width"]
    height = info["height"]

    command = [
        "ffmpeg",

        "-y",

        "-i",
        str(input_file),
    ]

    # --------------------------------------------------------
    # OPTIONAL 4K -> 1080P
    # --------------------------------------------------------

    if (
        convert_4k_to_1080p
        and (
            width >= 3840
            or height >= 2160
        )
    ):

        print(
            "   4K detected -> "
            "converting to 1080p"
        )

        command += [
            "-vf",
            "scale=1920:-2",
        ]

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    command += [

        "-c:v",
        "libx265",

        "-crf",
        str(CRF),

        "-preset",
        PRESET,

        "-pix_fmt",
        "yuv420p",
    ]

    # --------------------------------------------------------
    # AUDIO
    # --------------------------------------------------------

    command += [

        "-c:a",
        "aac",

        "-b:a",
        AUDIO_BITRATE,
    ]

    # --------------------------------------------------------
    # MP4
    # --------------------------------------------------------

    command += [

        "-movflags",
        "+faststart",

        str(output_file),
    ]

    subprocess.run(
        command,
        check=True,
    )


# ============================================================
# CREATE CSV ROW
# ============================================================

def create_report_row(
    input_file,
    output_file,
    original_info,
    compressed_info,
    original_size,
    compressed_size,
    start_time,
    end_time,
    conversion_seconds,
    status,
):

    reduction = (
        (
            1
            -
            compressed_size
            /
            original_size
        )
        * 100
        if original_size
        else 0
    )

    return {

        # ----------------------------------------------------
        # FILE
        # ----------------------------------------------------

        "File":
            str(input_file),

        "Output File":
            str(output_file),

        # ----------------------------------------------------
        # SIZE
        # ----------------------------------------------------

        "Original Size":
            format_size(
                original_size
            ),

        "Compressed Size":
            format_size(
                compressed_size
            ),

        "Reduction %":
            round(
                reduction,
                1,
            ),

        # ----------------------------------------------------
        # CONTAINER
        # ----------------------------------------------------

        "Original Container":
            original_info["container"],

        "Compressed Container":
            compressed_info["container"],

        "Compressed Container Name":
            compressed_info[
                "format_long_name"
            ],

        # ----------------------------------------------------
        # RESOLUTION
        # ----------------------------------------------------

        "Original Width":
            original_info["width"],

        "Original Height":
            original_info["height"],

        "Compressed Width":
            compressed_info["width"],

        "Compressed Height":
            compressed_info["height"],

        # ----------------------------------------------------
        # VIDEO CODEC
        # ----------------------------------------------------

        "Original Video Codec":
            original_info["video_codec"],

        "Compressed Video Codec":
            compressed_info["video_codec"],

        "Original Video Codec Name":
            original_info[
                "video_codec_long"
            ],

        "Compressed Video Codec Name":
            compressed_info[
                "video_codec_long"
            ],

        # ----------------------------------------------------
        # VIDEO PROFILE
        # ----------------------------------------------------

        "Original Video Profile":
            original_info[
                "video_profile"
            ],

        "Compressed Video Profile":
            compressed_info[
                "video_profile"
            ],

        # ----------------------------------------------------
        # VIDEO BITRATE
        # ----------------------------------------------------

        "Original Video Bitrate Kbps":
            format_bitrate(
                original_info[
                    "video_bitrate"
                ]
            ),

        "Compressed Video Bitrate Kbps":
            format_bitrate(
                compressed_info[
                    "video_bitrate"
                ]
            ),

        # ----------------------------------------------------
        # FPS
        # ----------------------------------------------------

        "Original FPS":
            format_fps(
                original_info["fps"]
            ),

        "Compressed FPS":
            format_fps(
                compressed_info["fps"]
            ),

        # ----------------------------------------------------
        # PIXEL FORMAT
        # ----------------------------------------------------

        "Original Pixel Format":
            original_info[
                "pixel_format"
            ],

        "Compressed Pixel Format":
            compressed_info[
                "pixel_format"
            ],

        # ----------------------------------------------------
        # VIDEO LEVEL
        # ----------------------------------------------------

        "Original Level":
            original_info["level"],

        "Compressed Level":
            compressed_info["level"],

        # ----------------------------------------------------
        # COLOR
        # ----------------------------------------------------

        "Original Color Space":
            original_info[
                "color_space"
            ],

        "Compressed Color Space":
            compressed_info[
                "color_space"
            ],

        "Original Color Transfer":
            original_info[
                "color_transfer"
            ],

        "Compressed Color Transfer":
            compressed_info[
                "color_transfer"
            ],

        "Original Color Primaries":
            original_info[
                "color_primaries"
            ],

        "Compressed Color Primaries":
            compressed_info[
                "color_primaries"
            ],

        "Original Color Range":
            original_info[
                "color_range"
            ],

        "Compressed Color Range":
            compressed_info[
                "color_range"
            ],

        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        "Original Audio Codec":
            original_info[
                "audio_codec"
            ],

        "Compressed Audio Codec":
            compressed_info[
                "audio_codec"
            ],

        "Original Audio Bitrate Kbps":
            format_bitrate(
                original_info[
                    "audio_bitrate"
                ]
            ),

        "Compressed Audio Bitrate Kbps":
            format_bitrate(
                compressed_info[
                    "audio_bitrate"
                ]
            ),

        "Original Audio Sample Rate":
            original_info[
                "audio_sample_rate"
            ],

        "Compressed Audio Sample Rate":
            compressed_info[
                "audio_sample_rate"
            ],

        "Original Audio Channels":
            original_info[
                "audio_channels"
            ],

        "Compressed Audio Channels":
            compressed_info[
                "audio_channels"
            ],

        "Original Audio Layout":
            original_info[
                "audio_channel_layout"
            ],

        "Compressed Audio Layout":
            compressed_info[
                "audio_channel_layout"
            ],

        # ----------------------------------------------------
        # DURATION
        # ----------------------------------------------------

        "Original Duration":
            format_duration(
                original_info[
                    "duration"
                ]
            ),

        "Compressed Duration":
            format_duration(
                compressed_info[
                    "duration"
                ]
            ),

        # ----------------------------------------------------
        # ENCODING TIME
        # ----------------------------------------------------

        "Start Time":
            start_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "End Time":
            end_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "Conversion Time":
            format_time(
                conversion_seconds
            ),

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        "Status":
            status,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("TUTORIAL VIDEO COMPRESSOR")
    print("=" * 80)
    print()

    # --------------------------------------------------------
    # SOURCE FOLDER
    # --------------------------------------------------------

    folder = input(
        "Enter the tutorial/course folder path:\n> "
    ).strip().strip('"')

    root = Path(folder)

    if not root.exists():

        print(
            "ERROR: Folder does not exist."
        )

        return

    if not root.is_dir():

        print(
            "ERROR: This is not a folder."
        )

        return

    # --------------------------------------------------------
    # 4K OPTION
    # --------------------------------------------------------

    print()
    print(
        "What should happen with 4K videos?"
    )

    print()
    print(
        "1. Keep 4K resolution"
    )

    print(
        "2. Convert 4K to 1080p"
    )

    print()

    choice = input(
        "Enter 1 or 2: "
    ).strip()

    if choice not in {
        "1",
        "2",
    }:

        print(
            "Invalid choice."
        )

        return

    convert_4k = (
        choice == "2"
    )

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    output_dir = (
        root / "compressed"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # FIND VIDEOS
    # --------------------------------------------------------

    videos = []

    for file_path in root.rglob("*"):

        if not file_path.is_file():
            continue

        if output_dir in file_path.parents:
            continue

        if (
            file_path.suffix.lower()
            not in VIDEO_EXTENSIONS
        ):
            continue

        videos.append(
            file_path
        )

    videos.sort()

    if not videos:

        print(
            "No video files found."
        )

        return

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 80)

    print(
        f"Videos found : "
        f"{len(videos)}"
    )

    print(
        "Codec        : H.265 / HEVC"
    )

    print(
        f"CRF          : {CRF}"
    )

    print(
        f"Preset       : {PRESET}"
    )

    print(
        f"Audio        : AAC {AUDIO_BITRATE}"
    )

    if convert_4k:

        print(
            "4K           : 4K -> 1080p"
        )

    else:

        print(
            "4K           : Keep 4K"
        )

    print("=" * 80)

    # --------------------------------------------------------
    # CONFIRM
    # --------------------------------------------------------

    print()

    confirm = input(
        "Start compression? (y/n): "
    ).strip().lower()

    if confirm != "y":

        print(
            "Cancelled."
        )

        return

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    report = []

    # --------------------------------------------------------
    # PROCESS
    # --------------------------------------------------------

    for index, input_file in enumerate(
        videos,
        start=1,
    ):

        relative_path = (
            input_file.relative_to(
                root
            )
        )

        output_file = (
            output_dir /
            relative_path
        )

        output_file = (
            output_file.with_suffix(
                ".mp4"
            )
        )

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        print()
        print("=" * 80)

        print(
            f"[{index}/{len(videos)}]"
        )

        print(
            input_file.name
        )

        print("=" * 80)

        original_size = (
            input_file.stat().st_size
        )

        # ----------------------------------------------------
        # SKIP EXISTING
        # ----------------------------------------------------

        if output_file.exists():

            print(
                "✓ Compressed file "
                "already exists."
            )

            print(
                "Skipping..."
            )

            # -----------------------------------------------
            # IMPORTANT:
            # Inspect BOTH existing files
            # -----------------------------------------------

            try:

                original_info = (
                    get_video_info(
                        input_file
                    )
                )

                compressed_info = (
                    get_video_info(
                        output_file
                    )
                )

                compressed_size = (
                    output_file.stat().st_size
                )

                row = create_report_row(

                    input_file,

                    output_file,

                    original_info,

                    compressed_info,

                    original_size,

                    compressed_size,

                    datetime.fromtimestamp(
                        output_file.stat().st_mtime
                    ),

                    datetime.fromtimestamp(
                        output_file.stat().st_mtime
                    ),

                    0,

                    "Already exists - skipped",
                )

                report.append(row)

            except Exception as error:

                print(
                    f"Could not inspect "
                    f"existing file: {error}"
                )

            continue

        # ----------------------------------------------------
        # GET ORIGINAL INFO
        # ----------------------------------------------------

        try:

            print(
                "Reading source information..."
            )

            original_info = (
                get_video_info(
                    input_file
                )
            )

            print(
                f"Resolution : "
                f"{original_info['width']}x"
                f"{original_info['height']}"
            )

            print(
                f"Codec      : "
                f"{original_info['video_codec']}"
            )

            print(
                f"Bitrate    : "
                f"{format_bitrate(original_info['video_bitrate'])} kbps"
            )

            print(
                f"Duration   : "
                f"{format_duration(original_info['duration'])}"
            )

            print(
                f"Original   : "
                f"{format_size(original_size)}"
            )

            # ------------------------------------------------
            # START
            # ------------------------------------------------

            start_time = datetime.now()

            start_counter = (
                time.perf_counter()
            )

            print()
            print(
                "Compressing..."
            )

            # ------------------------------------------------
            # COMPRESS
            # ------------------------------------------------

            compress_video(

                input_file,

                output_file,

                convert_4k,
            )

            # ------------------------------------------------
            # END
            # ------------------------------------------------

            end_counter = (
                time.perf_counter()
            )

            end_time = (
                datetime.now()
            )

            conversion_seconds = (
                end_counter
                -
                start_counter
            )

            # ------------------------------------------------
            # VERIFY
            # ------------------------------------------------

            if not output_file.exists():

                raise RuntimeError(
                    "Output file was not created."
                )

            compressed_size = (
                output_file.stat().st_size
            )

            # ------------------------------------------------
            # INSPECT COMPRESSED FILE
            # ------------------------------------------------

            print()
            print(
                "Inspecting compressed file..."
            )

            compressed_info = (
                get_video_info(
                    output_file
                )
            )

            # ------------------------------------------------
            # DISPLAY
            # ------------------------------------------------

            reduction = (
                (
                    1
                    -
                    compressed_size
                    /
                    original_size
                )
                * 100
            )

            print()
            print("✓ DONE")

            print(
                f"Original   : "
                f"{format_size(original_size)}"
            )

            print(
                f"Compressed : "
                f"{format_size(compressed_size)}"
            )

            print(
                f"Reduction  : "
                f"{reduction:.1f}%"
            )

            print(
                f"New codec  : "
                f"{compressed_info['video_codec']}"
            )

            print(
                f"New bitrate: "
                f"{format_bitrate(compressed_info['video_bitrate'])} kbps"
            )

            print(
                f"New resolution: "
                f"{compressed_info['width']}x"
                f"{compressed_info['height']}"
            )

            print(
                f"Conversion time: "
                f"{format_time(conversion_seconds)}"
            )

            # ------------------------------------------------
            # REPORT
            # ------------------------------------------------

            row = create_report_row(

                input_file,

                output_file,

                original_info,

                compressed_info,

                original_size,

                compressed_size,

                start_time,

                end_time,

                conversion_seconds,

                "Success",
            )

            report.append(row)

        except Exception as error:

            print()
            print(
                "✗ ERROR"
            )

            print(error)

            report.append({

                "File":
                    str(input_file),

                "Output File":
                    "",

                "Original Size":
                    format_size(
                        original_size
                    ),

                "Compressed Size":
                    "",

                "Reduction %":
                    "",

                "Original Container":
                    "",

                "Compressed Container":
                    "",

                "Compressed Container Name":
                    "",

                "Original Width":
                    "",

                "Original Height":
                    "",

                "Compressed Width":
                    "",

                "Compressed Height":
                    "",

                "Original Video Codec":
                    "",

                "Compressed Video Codec":
                    "",

                "Original Video Codec Name":
                    "",

                "Compressed Video Codec Name":
                    "",

                "Original Video Profile":
                    "",

                "Compressed Video Profile":
                    "",

                "Original Video Bitrate Kbps":
                    "",

                "Compressed Video Bitrate Kbps":
                    "",

                "Original FPS":
                    "",

                "Compressed FPS":
                    "",

                "Original Pixel Format":
                    "",

                "Compressed Pixel Format":
                    "",

                "Original Level":
                    "",

                "Compressed Level":
                    "",

                "Original Color Space":
                    "",

                "Compressed Color Space":
                    "",

                "Original Color Transfer":
                    "",

                "Compressed Color Transfer":
                    "",

                "Original Color Primaries":
                    "",

                "Compressed Color Primaries":
                    "",

                "Original Color Range":
                    "",

                "Compressed Color Range":
                    "",

                "Original Audio Codec":
                    "",

                "Compressed Audio Codec":
                    "",

                "Original Audio Bitrate Kbps":
                    "",

                "Compressed Audio Bitrate Kbps":
                    "",

                "Original Audio Sample Rate":
                    "",

                "Compressed Audio Sample Rate":
                    "",

                "Original Audio Channels":
                    "",

                "Compressed Audio Channels":
                    "",

                "Original Audio Layout":
                    "",

                "Compressed Audio Layout":
                    "",

                "Original Duration":
                    "",

                "Compressed Duration":
                    "",

                "Start Time":
                    "",

                "End Time":
                    "",

                "Conversion Time":
                    "",

                "Status":
                    f"ERROR: {error}",
            })

    # ========================================================
    # WRITE CSV
    # ========================================================

    report_file = (
        output_dir /
        "compression_report.csv"
    )

    fieldnames = [

        "File",
        "Output File",

        "Original Size",
        "Compressed Size",
        "Reduction %",

        "Original Container",
        "Compressed Container",
        "Compressed Container Name",

        "Original Width",
        "Original Height",
        "Compressed Width",
        "Compressed Height",

        "Original Video Codec",
        "Compressed Video Codec",

        "Original Video Codec Name",
        "Compressed Video Codec Name",

        "Original Video Profile",
        "Compressed Video Profile",

        "Original Video Bitrate Kbps",
        "Compressed Video Bitrate Kbps",

        "Original FPS",
        "Compressed FPS",

        "Original Pixel Format",
        "Compressed Pixel Format",

        "Original Level",
        "Compressed Level",

        "Original Color Space",
        "Compressed Color Space",

        "Original Color Transfer",
        "Compressed Color Transfer",

        "Original Color Primaries",
        "Compressed Color Primaries",

        "Original Color Range",
        "Compressed Color Range",

        "Original Audio Codec",
        "Compressed Audio Codec",

        "Original Audio Bitrate Kbps",
        "Compressed Audio Bitrate Kbps",

        "Original Audio Sample Rate",
        "Compressed Audio Sample Rate",

        "Original Audio Channels",
        "Compressed Audio Channels",

        "Original Audio Layout",
        "Compressed Audio Layout",

        "Original Duration",
        "Compressed Duration",

        "Start Time",
        "End Time",
        "Conversion Time",

        "Status",
    ]

    with open(
        report_file,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()

        writer.writerows(report)

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    successful = [

        row

        for row in report

        if row.get("Compressed Size")
    ]

    print()
    print()
    print("=" * 80)
    print("COMPRESSION COMPLETE")
    print("=" * 80)

    print(
        f"Videos processed : "
        f"{len(videos)}"
    )

    print()
    print(
        "CSV report:"
    )

    print(
        report_file
    )

    print()
    print(
        "Compressed folder:"
    )

    print(
        output_dir
    )

    print("=" * 80)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()