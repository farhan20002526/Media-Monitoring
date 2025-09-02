import os
import subprocess
import time

# Temp folder for saving chunks
temp_folder = './temp'  # Temporary folder for storing chunks
os.makedirs(temp_folder, exist_ok=True)

def save_chunks(input_video, chunk_duration_seconds=300):
    try:
        chunk_count = 1
        total_duration_processed = 0

        while True:
            # Get the current time1
            current_time = time.time()

            # Calculate the start time for the next chunk aligned to the next minute
            next_chunk_time = current_time + chunk_duration_seconds - (current_time % chunk_duration_seconds)

            # Wait until the next chunk time
            time_to_wait = next_chunk_time - current_time
            if time_to_wait > 0:
                time.sleep(time_to_wait)

            now = time.strftime("%Y%m%d_%H%M%S")
            # Use forward slashes for the file path template
            chunk_outputfile = os.path.join(temp_folder, f"chunk_{now}_{chunk_count:03d}.mp4").replace('\\', '/')

            # Calculate the start time for the current chunk
            start_time = total_duration_processed

            # Use ffmpeg to create a segment of the video
            ffmpeg_command = [
                'ffmpeg',
                '-ss', str(start_time),
                '-i', input_video,
                '-t', str(chunk_duration_seconds),
                '-c', 'copy',
                chunk_outputfile
            ]

            # Run ffmpeg command and capture stderr
            result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)

            print(f"Saved chunk {chunk_count}: {chunk_outputfile}")

            # Update the total duration processed
            total_duration_processed += chunk_duration_seconds
            chunk_count += 1

    except subprocess.CalledProcessError as e:
        print(f"ffmpeg command failed: {e}")
        print(f"ffmpeg stderr: {e.stderr}")
    except Exception as e:
        print(f"An error occurred during chunk saving: {str(e)}")

# Example usage
if __name__ == "__main__":
    input_video = './downloads/2025-5-27-1657_raw.mp4.part'  # Adjust with actual path
    save_chunks(input_video, chunk_duration_seconds=300)
