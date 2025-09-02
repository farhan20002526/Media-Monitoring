from yt_dlp import YoutubeDL

def download_youtube_video(link):
    try:
        # Add verbose logs to debug
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'D:/Proxima/works/youtube downloader/youtube-stream-downloader/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'postprocessors': [
                {
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }
            ],
            'verbose': True,  # Enable verbose logs for debugging
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
    except Exception as e:
        print(f"An error occurred: {e}")

# Replace the link with your YouTube video URL
youtube_link = "https://www.youtube.com/watch?v=uz3v9joxAx0"
download_youtube_video(youtube_link)
