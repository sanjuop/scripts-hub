"""
Self Timer - Keep-Alive Utility
Prevents Windows from sleeping, turning off the display, or entering idle lock.

Features:
- Visible mouse movement (random coordinates or visible wiggle)
- Instant first pulse on start (you immediately see it work)
- Native Windows API power keep-awake active in all modes
- 0% CPU utilization (optimized sleep loop)
- Configurable interval, timeout duration, or stop-at time
"""

import sys
import time
import random
import datetime
import argparse
import ctypes

# Windows Execution State flags for power management
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def set_keep_awake():
    """Instruct Windows that the system and display are in active use."""
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )
    except Exception as e:
        print(f"[Warning] Failed to set thread execution state: {e}", flush=True)


def reset_keep_awake():
    """Restore normal Windows power management behavior."""
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    except Exception:
        pass


def get_screen_resolution():
    """Get screen width and height in pixels."""
    try:
        w = ctypes.windll.user32.GetSystemMetrics(0)
        h = ctypes.windll.user32.GetSystemMetrics(1)
        return max(800, w), max(600, h)
    except Exception:
        return 1920, 1080


def get_cursor_pos():
    """Get current cursor position."""
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def move_cursor_random():
    """Visibly move the mouse cursor to a random screen coordinate."""
    width, height = get_screen_resolution()
    # Keep away from screen edges/taskbar slightly
    target_x = random.randint(100, max(150, width - 100))
    target_y = random.randint(100, max(150, height - 100))
    ctypes.windll.user32.SetCursorPos(target_x, target_y)
    return target_x, target_y


def move_cursor_wiggle(distance=50):
    """Visibly wiggle the cursor back and forth from its current position."""
    x, y = get_cursor_pos()
    ctypes.windll.user32.SetCursorPos(x + distance, y)
    time.sleep(0.15)
    ctypes.windll.user32.SetCursorPos(x, y)
    return x, y


def parse_arguments():
    parser = argparse.ArgumentParser(description="Keep Windows active and prevent screen timeout/sleep.")
    parser.add_argument(
        "--mode",
        choices=["random", "wiggle", "stealth"],
        default="random",
        help="Keep-awake mode: 'random' (moves cursor to random position), 'wiggle' (nudges back and forth), 'stealth' (Windows API only, no movement) (default: random)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Interval between keep-alive pulses in seconds (default: 30s)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Total duration to run in minutes (0 = run indefinitely until stopped, default: 0)"
    )
    parser.add_argument(
        "--until",
        type=str,
        default="",
        help="Optional exit time in HH:MM or HH:MM:SS format (e.g. 19:30:00)"
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    start_time = time.time()
    width, height = get_screen_resolution()

    print("=" * 65, flush=True)
    print(" KEEP-ALIVE SYSTEM ACTIVE", flush=True)
    print("=" * 65, flush=True)
    print(f" Screen Resolution : {width}x{height}", flush=True)
    print(f" Movement Mode     : {args.mode.upper()}", flush=True)
    print(f" Interval          : Every {args.interval} seconds", flush=True)
    if args.duration > 0:
        print(f" Duration          : {args.duration} minutes", flush=True)
    elif args.until:
        print(f" Stop At           : {args.until}", flush=True)
    else:
        print(" Duration          : Indefinite (click Stop or Ctrl+C to exit)", flush=True)
    print(" CPU Usage         : ~0.0% (Optimized sleep loop)", flush=True)
    print("=" * 65, flush=True)
    print("[Info] Keep-awake running. Moving cursor immediately...\n", flush=True)

    # Initial keep-awake activation
    set_keep_awake()

    # Trigger first pulse immediately so user gets instant visual confirmation!
    next_pulse = time.time()
    pulse_count = 0

    try:
        while True:
            now = time.time()
            current_time = datetime.datetime.now()

            # Check duration expiry
            if args.duration > 0 and (now - start_time) >= (args.duration * 60):
                print(f"[Done] Reached configured duration of {args.duration} minutes.", flush=True)
                break

            # Check specific target time
            if args.until:
                time_str = current_time.strftime("%H:%M:%S")
                if time_str >= args.until:
                    print(f"[Done] Reached target time {args.until}.", flush=True)
                    break

            # Pulse keep-awake
            if now >= next_pulse:
                pulse_count += 1
                timestamp = current_time.strftime("%H:%M:%S")

                # Always refresh Windows API state
                set_keep_awake()

                if args.mode == "random":
                    x, y = move_cursor_random()
                    print(f"[{timestamp}] Pulse #{pulse_count}: Cursor visibly moved to ({x}, {y})", flush=True)
                elif args.mode == "wiggle":
                    x, y = move_cursor_wiggle()
                    print(f"[{timestamp}] Pulse #{pulse_count}: Cursor wiggled at ({x}, {y})", flush=True)
                else:  # stealth
                    print(f"[{timestamp}] Pulse #{pulse_count}: Windows keep-awake active (Stealth mode)", flush=True)

                next_pulse = now + args.interval

            # Efficient 1-second sleep to keep CPU at 0%
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[Stopped] Keep-awake stopped by user.", flush=True)
    finally:
        reset_keep_awake()
        print("[Status] Restored default Windows power settings.", flush=True)


if __name__ == "__main__":
    main()
