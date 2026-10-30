# yt-dlp -x --audio-format mp3 -o "D:\Whisper\3dHonest.mp3" "https://www.youtube.com/watch?v=ivxstvYb43g"

#ffmpeg -i "D:\sAS\[BadMILFS] Gal Richie, Kenzie Taylor (We’re the Taylors Time for a Getaway.mkv" -c copy "D:\temp\ls.mp4"

# __path = r"D:\blenderPhysics\Coloso_-_The_59-Chapter_Guide_to_Blender_Physics_Simulators_That_Overcome_3D_Limits\Section_01-Intro"
# import os
# import subprocess
# allFiles = [i for i in os.listdir(__path) if i.endswith(".mp4")]
# for i in allFiles:
#     videoPath = os.path.join(__path, i)
#     audioPath = videoPath.replace(".mp4", ".wav")
#     output = videoPath.replace(".mp4", "_eng.mp4")
#     cmd = r'C:\ffmpeg\ffmpeg.exe -i {} -i {} -c:v copy -c:a aac -map 0:v -map 1:a {}'.format(videoPath, audioPath, output)
#     print(cmd)
#     subprocess.call(cmd)
#     print("***********************************************************************************************")


# __path = r"D:\Editing\Chapter07-Copy"
# import os
# import subprocess
# allFiles = [i for i in os.listdir(__path) if i.endswith(".ts")]
# for i in allFiles:
#     videoPath = os.path.join(__path, i)
#     audioPath = videoPath.replace(".ts", ".m4a")
#     cmd = r'ffmpeg -i "{}" -map 0:a -acodec copy "{}"'.format(videoPath, audioPath)
#     print(cmd)
#     subprocess.call(cmd)
#     print("***********************************************************************************************")

import os
import subprocess

__path = r"D:\Lighting\Tom_Noske_Video_Creator Academy_MP4\3_Mastering_Scene_Creation_[Practical_Lessons]"

# Supported video formats (expandable)
VIDEO_FORMATS = [".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv", ".webm", "mp3", ".ts"]

# Get all video files (case-insensitive check)
video_files = [
    file for file in os.listdir(__path) 
    if any(file.lower().endswith(ext) for ext in VIDEO_FORMATS)
]

for video_file in video_files:
    video_path = os.path.join(__path, video_file)
    if "Downloads" in video_path:
        continue
    basename = os.path.splitext(video_file)[0]
    
    # Check if transcript files already exist
    txt_exists = os.path.exists(os.path.join(__path, f"{basename}.txt"))
    srt_exists = os.path.exists(os.path.join(__path, f"{basename}.srt"))
    print("txt_exists",txt_exists)
    print("srt_exists",srt_exists)  
    if txt_exists or srt_exists:
        print(f"Skipping {video_file} - transcript already exists")
        print("-" * 80)
        continue
    
    # Run Whisper if no transcript exists
    # cmd = f'whisper "{video_path}" --output_dir "{__path}" --model small --language Russian --task translate --output_format srt'
    # cmd = f'whisper "{video_path}" --output_dir "{__path}" --model tiny --language English --output_format srt'
    cmd = f'whisper "{video_path}" --output_dir "{__path}" --model tiny --language English --word_timestamps True --output_format json'
    print("Running:", cmd)
    
    subprocess.call(cmd, shell=True)
    print("-" * 80)





# __path = r"D:\DavinciTut\Working_with_Sound_in_DaVinci_Resolve_Fairlight_(2024)\Lesson_1_Fairlight_Interface_Overview_and_Basic_Functions"
# import os
# import subprocess
# formats = [".mp4", ".mkv"]
# print("os.listdir(__path)", os.listdir(__path))
# allFiles = [file for file in os.listdir(__path) if file.lower().endswith(tuple(formats))]
# print("allFiles", allFiles)
# for i in allFiles:
#     videoPath = os.path.join(__path, i)
#     basenameWIthExt = os.path.basename(videoPath)
#     print("basenameWIthExt", basenameWIthExt)
#     format = [basenameWIthExt.split(i)[1] for i in formats if i.endswith(tuple(formats))]
#     print("format", format)
#     textFile = videoPath.replace(format, ".txt")
#     print("textFile", textFile)
#     basename = basenameWIthExt.split(format)
#     print("basename", basename)
#     newFolder = os.path.join(__path, basename)
#     print("newFolder", newFolder)
#     if not os.path.exists(newFolder):
#         print("newFolder1")
#         os.makedirs(newFolder)
#         cmd = r'whisper "{}" --output_dir {} --model small --language Russian --task translate'.format(videoPath, newFolder)
#         print(cmd)
#         subprocess.call(cmd)
#         print("***********************************************************************************************")
    # if not os.path.exists(textFile):
    #     # cmd = r'whisper "{}" --output_dir {} --model tiny --language English --output_format txt'.format(videoPath, __path)
    #     cmd = r'whisper "{}" --output_dir {} --model small --language Russian --task translate'.format(videoPath, __path)
    #     print(cmd)
    #     subprocess.call(cmd)
    #     print("***********************************************************************************************")




# import os

# def rename_files_and_folders(root_dir):
#     for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
#         # Rename files
#         for filename in filenames:
#             if ' ' in filename:
#                 new_filename = filename.replace(' ', '_')
#                 old_file_path = os.path.join(dirpath, filename)
#                 new_file_path = os.path.join(dirpath, new_filename)
#                 os.rename(old_file_path, new_file_path)
#                 print(f'Renamed file: {old_file_path} -> {new_file_path}')
        
#         # Rename directories
#         for dirname in dirnames:
#             if ' ' in dirname:
#                 new_dirname = dirname.replace(' ', '_')
#                 old_dir_path = os.path.join(dirpath, dirname)
#                 new_dir_path = os.path.join(dirpath, new_dirname)
#                 os.rename(old_dir_path, new_dir_path)
#                 print(f'Renamed directory: {old_dir_path} -> {new_dir_path}')

# # Example usage
# root_dir = r'D:\DavinciTut\Working_with_Sound_in_DaVinci_Resolve_Fairlight_(2024)'
# rename_files_and_folders(root_dir)
