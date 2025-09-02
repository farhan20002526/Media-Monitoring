import os
import subprocess
import datetime
import logging
import time
import psutil  # Add this import for checking if a process is running

temp_folder = "./temp"
output_dir = "./downloads"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define function to capture frames at a fixed rate and specific coordinates using ffmpeg
def capture_frames_fixed_rate_and_crop(input_video, output_dir, frame_rate, x, y, width, height):
    try:
        # Create 'frames' directory if it doesn't exist within output_dir
        frames_dir = os.path.join(output_dir, 'frames')
        os.makedirs(frames_dir, exist_ok=True)

        # Generate timestamp for unique filenames
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Construct output file template in 'frames' directory
        output_template = os.path.join(frames_dir, f"frame_{timestamp}_%04d.png")

        # Construct ffmpeg command for fixed frame rate and crop
        ffmpeg_command = [
            'ffmpeg',
            '-i', input_video,
            '-vf', f'crop={width}:{height}:{x}:{y},fps={frame_rate}',
            output_template
        ]

        logging.info(f"Capturing frames from {input_video} at fixed frame rate {frame_rate} and coordinates ({x}, {y}) with width {width} and height {height}")
        logging.info(f"Command: {' '.join(ffmpeg_command)}")

        # Run ffmpeg command and capture stderr
        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)

        logging.info(f"Return code: {result.returncode}")
        if result.returncode == 0:
            logging.info("Frames captured successfully.")
        else:
            logging.error("Frame capture failed.")
            logging.error(result.stderr)  # Print ffmpeg stderr output

    except Exception as e:
        logging.error(f"An error occurred during frame capture: {str(e)}")

def is_video_generated(video_file):
    # Function to check if the video file exists and is complete
    if not os.path.exists(video_file):
        return False
    
    initial_size = os.path.getsize(video_file)
    time.sleep(10)  # Wait for 10 seconds before checking size again (adjust as needed)
    new_size = os.path.getsize(video_file)
    
    return initial_size == new_size and initial_size > 0

def is_live_script_running(script_name):
    # Check if the specified script is running
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        cmdline = proc.info['cmdline']
        if cmdline and script_name in cmdline:
            return True
    return False

def get_video_files(directory):
    # Function to get list of video files in a directory
    video_files = []
    for filename in os.listdir(directory):
        if filename.endswith(".mp4"):  # Adjust file extension as per your case
            video_files.append(os.path.join(directory, filename))
    return video_files

if __name__ == "__main__":
    frame_rate = '1/8'  # Frame rate for capturing frames (1 frame every 9 seconds)
    x = 0  # X-coordinate (left edge of the cropping area)
    y = 630  # Y-coordinate (top edge of the cropping area)
    width = 854  # Width of the cropping area
    height = 100  # Height of the cropping area

    processed_files = set()

    while True:
        # Check if the live script is still running
        if not is_live_script_running("chunk_wise.py"):
            logging.info("Live script has terminated. Stopping frame capture.")
            break

        video_files = get_video_files(temp_folder)

        for video_file in video_files:
            if video_file in processed_files:
                continue

            while not is_video_generated(video_file):
                logging.info(f"Waiting for {video_file} to be generated...")
                time.sleep(10)  # Wait before checking again

            capture_frames_fixed_rate_and_crop(video_file, output_dir, frame_rate, x, y, width, height)
            processed_files.add(video_file)

        # Introduce a delay before checking for new video files
        time.sleep(10)  # Adjust delay as needed
