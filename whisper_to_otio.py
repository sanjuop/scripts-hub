
import json
from pathlib import Path

import opentimelineio as otio


# ============================================================
# CONFIGURATION
# ============================================================

VIDEO_FILE = Path(r"D:\asd\AITest\sample_short.mp4")
JSON_FILE = Path(r"D:\asd\AITest\sample_short.json")


# Remove pauses >= this duration
MIN_SILENCE = 0.7


# Keep a small amount of silence around speech.
#
# Example:
#
# Previous speech ends: 21.92
# Next speech starts:   23.68
#
# Instead of removing:
#
# 21.92 -> 23.68
#
# we keep:
#
# 21.92 -> 22.07   (0.15 sec)
# 23.53 -> 23.68   (0.15 sec)
#
# and remove:
#
# 22.07 -> 23.53
#
KEEP_SILENCE = 0.05


# Timeline frame rate
FPS = 24


# ============================================================
# OUTPUT FILES
# ============================================================

OTIO_FILE = VIDEO_FILE.with_name(
    VIDEO_FILE.stem + "_AI_Edit.otio"
)

EDL_FILE = VIDEO_FILE.with_name(
    VIDEO_FILE.stem + "_AI_Edit.txt"
)


# ============================================================
# LOAD WHISPER JSON
# ============================================================

def load_whisper_json():

    with open(
        JSON_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# EXTRACT WORDS
# ============================================================

def get_words(data):

    words = []

    for segment in data.get("segments", []):

        for word in segment.get("words", []):

            words.append({
                "word": word["word"],
                "start": float(word["start"]),
                "end": float(word["end"]),
                "probability": float(
                    word.get("probability", 1.0)
                )
            })

    return words


# ============================================================
# CREATE KEEP RANGES
# ============================================================

def create_keep_ranges(words):

    if not words:
        return [], []

    keep_ranges = []
    removed_sections = []

    # --------------------------------------------------------
    # IMPORTANT
    #
    # Start from the beginning of the video.
    #
    # We don't want to remove the beginning just because
    # Whisper detected the first word slightly later.
    # --------------------------------------------------------

    current_start = 0.0

    previous_end = words[0]["end"]

    for word in words[1:]:

        word_start = word["start"]
        word_end = word["end"]

        # ----------------------------------------------------
        # Calculate silence between two words
        # ----------------------------------------------------

        gap = word_start - previous_end

        if gap >= MIN_SILENCE:

            # ------------------------------------------------
            # Protect speech on both sides of the cut.
            # ------------------------------------------------

            cut_start = previous_end + KEEP_SILENCE

            cut_end = word_start - KEEP_SILENCE

            # ------------------------------------------------
            # Safety check.
            #
            # If the silence is too short after adding the
            # protection margins, don't remove anything.
            # ------------------------------------------------

            if cut_end > cut_start:

                # --------------------------------------------
                # Keep everything before the removed silence.
                # --------------------------------------------

                keep_ranges.append(
                    (
                        current_start,
                        cut_start
                    )
                )

                # --------------------------------------------
                # The next clip starts AFTER the removed
                # silence.
                # --------------------------------------------

                current_start = cut_end

                # --------------------------------------------
                # Store information for the edit report.
                # --------------------------------------------

                removed_sections.append({
                    "start": cut_start,
                    "end": cut_end,
                    "duration": cut_end - cut_start,
                    "original_silence": gap,
                    "next_word": word["word"]
                })

        # ----------------------------------------------------
        # Always update previous word end.
        # ----------------------------------------------------

        previous_end = word_end

    # ========================================================
    # FINAL SECTION
    # ========================================================

    keep_ranges.append(
        (
            current_start,
            previous_end
        )
    )

    return keep_ranges, removed_sections


# ============================================================
# FORMAT SECONDS
# ============================================================

def seconds_to_time(seconds):

    hours = int(
        seconds // 3600
    )

    minutes = int(
        (seconds % 3600) // 60
    )

    secs = seconds % 60

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:06.3f}"
    )


# ============================================================
# WRITE HUMAN-READABLE EDIT LIST
# ============================================================

def write_edit_list(
    keep_ranges,
    removed_sections
):

    with open(
        EDL_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        # ====================================================
        # HEADER
        # ====================================================

        f.write(
            "AI VIDEO EDIT DECISION LIST\n"
        )

        f.write(
            "=" * 70
            + "\n\n"
        )

        # ====================================================
        # KEEP RANGES
        # ====================================================

        f.write(
            "KEEP RANGES\n"
        )

        f.write(
            "-" * 70
            + "\n\n"
        )

        for index, (
            start,
            end
        ) in enumerate(
            keep_ranges,
            start=1
        ):

            f.write(
                f"KEEP {index:03d}  "
                f"{seconds_to_time(start)} -> "
                f"{seconds_to_time(end)}\n"
            )

        # ====================================================
        # REMOVED SILENCES
        # ====================================================

        f.write(
            "\n\n"
        )

        f.write(
            "REMOVED SILENCES\n"
        )

        f.write(
            "-" * 70
            + "\n\n"
        )

        for index, section in enumerate(
            removed_sections,
            start=1
        ):

            f.write(
                f"CUT {index:03d}\n"
            )

            f.write(
                f"  Original silence : "
                f"{seconds_to_time(section['start'] - KEEP_SILENCE)}"
                f" -> "
                f"{seconds_to_time(section['end'] + KEEP_SILENCE)}\n"
            )

            f.write(
                f"  Removed section  : "
                f"{seconds_to_time(section['start'])}"
                f" -> "
                f"{seconds_to_time(section['end'])}\n"
            )

            f.write(
                f"  Removed duration : "
                f"{section['duration']:.3f} sec\n"
            )

            f.write(
                f"  Next word        : "
                f"{section['next_word'].strip()}\n"
            )

            f.write(
                "\n"
            )

    print(
        f"Edit list: {EDL_FILE}"
    )


# ============================================================
# CREATE OTIO MEDIA REFERENCE
# ============================================================

def create_media_reference():

    return otio.schema.ExternalReference(
        target_url=VIDEO_FILE.resolve().as_uri()
    )


# ============================================================
# CREATE OTIO TIMELINE
# ============================================================

def create_timeline(
    keep_ranges
):

    timeline = otio.schema.Timeline(
        name=f"{VIDEO_FILE.stem}_AI_Edit"
    )

    # ========================================================
    # VIDEO TRACK
    # ========================================================

    video_track = otio.schema.Track(
        name="V1",
        kind=otio.schema.TrackKind.Video
    )

    # ========================================================
    # AUDIO TRACK
    # ========================================================

    audio_track = otio.schema.Track(
        name="A1",
        kind=otio.schema.TrackKind.Audio
    )

    # ========================================================
    # MEDIA REFERENCE
    # ========================================================

    media_reference = create_media_reference()

    # ========================================================
    # CREATE CLIPS
    # ========================================================

    for index, (
        source_start,
        source_end
    ) in enumerate(
        keep_ranges,
        start=1
    ):

        duration = (
            source_end
            - source_start
        )

        # ----------------------------------------------------
        # SOURCE RANGE
        # ----------------------------------------------------

        source_range = otio.opentime.TimeRange(

            start_time=otio.opentime.RationalTime(
                value=source_start * FPS,
                rate=FPS
            ),

            duration=otio.opentime.RationalTime(
                value=duration * FPS,
                rate=FPS
            )
        )

        # ====================================================
        # VIDEO CLIP
        # ====================================================

        video_clip = otio.schema.Clip(
            name=f"AI_Cut_{index:03d}",
            media_reference=media_reference,
            source_range=source_range
        )

        video_track.append(
            video_clip
        )

        # ====================================================
        # AUDIO CLIP
        # ====================================================

        audio_clip = otio.schema.Clip(
            name=f"AI_Cut_{index:03d}_Audio",
            media_reference=media_reference,
            source_range=source_range
        )

        audio_track.append(
            audio_clip
        )

    # ========================================================
    # ADD TRACKS
    # ========================================================

    timeline.tracks.append(
        video_track
    )

    timeline.tracks.append(
        audio_track
    )

    return timeline


# ============================================================
# WRITE OTIO
# ============================================================

def write_otio(
    timeline
):

    otio.adapters.write_to_file(
        timeline,
        str(OTIO_FILE)
    )

    print(
        f"OTIO timeline: {OTIO_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "Loading Whisper JSON..."
    )

    # --------------------------------------------------------
    # Load JSON
    # --------------------------------------------------------

    data = load_whisper_json()

    # --------------------------------------------------------
    # Extract words
    # --------------------------------------------------------

    words = get_words(
        data
    )

    print(
        f"Words found: {len(words)}"
    )

    # --------------------------------------------------------
    # Create keep ranges
    # --------------------------------------------------------

    (
        keep_ranges,
        removed_sections
    ) = create_keep_ranges(
        words
    )

    print(
        f"Keep sections: "
        f"{len(keep_ranges)}"
    )

    print(
        f"Removed silences: "
        f"{len(removed_sections)}"
    )

    # ========================================================
    # PRINT DETECTED CUTS
    # ========================================================

    print()
    print(
        "Detected silence cuts:"
    )

    print(
        "-" * 70
    )

    for index, section in enumerate(
        removed_sections,
        start=1
    ):

        print(
            f"CUT {index:03d}: "
            f"removed "
            f"{section['duration']:.3f}s | "
            f"{seconds_to_time(section['start'])} -> "
            f"{seconds_to_time(section['end'])} | "
            f"next word: "
            f"{section['next_word'].strip()}"
        )

    # ========================================================
    # WRITE EDIT REPORT
    # ========================================================

    write_edit_list(
        keep_ranges,
        removed_sections
    )

    # ========================================================
    # CREATE OTIO
    # ========================================================

    timeline = create_timeline(
        keep_ranges
    )

    # ========================================================
    # WRITE OTIO
    # ========================================================

    write_otio(
        timeline
    )

    # ========================================================
    # DONE
    # ========================================================

    print()
    print(
        "========================================"
    )

    print(
        "OTIO TIMELINE CREATED"
    )

    print(
        "========================================"
    )

    print()
    print(
        "Original video was NOT modified."
    )

    print()
    print(
        "Open this file in DaVinci Resolve:"
    )

    print(
        OTIO_FILE
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
