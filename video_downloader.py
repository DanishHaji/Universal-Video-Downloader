import streamlit as st
import yt_dlp
import os
import time
import re

# Page Config
st.set_page_config(page_title="Universal Video Downloader", page_icon="📹", layout="centered")

st.markdown("""
    <style>
        .stTextInput, .stSelectbox, .stRadio, .stButton {
            margin-left: auto;
            margin-right: auto;
        }
        .stTextInput input, .stSelectbox select {
            border: 2px solid #FF4B4B;
        }
        .stButton button {
            background-color: #FF4B4B;
            color: white;
        }
        .success-msg {
            color: #4CAF50;
            font-weight: bold;
            padding: 10px;
            border-radius: 5px;
            background-color: #E8F5E9;
            text-align: center;
        }
        .stImage {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-top: 20px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📹 Universal Video Downloader")
st.markdown("Download videos from **any platform** in your desired resolution, or extract audio as MP3.")

# Utility
def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename).replace(" ", "_")

def get_video_info(url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail', None),
                'duration': info.get('duration', 0),
                'formats': info.get('formats', [])
            }
    except Exception as e:
        st.error(f"❌ Error getting video info: {str(e)}")
        return None

def download_video(url, format_type, resolution, audio_bitrate=None):
    try:
        os.makedirs('downloads', exist_ok=True)

        if format_type == "audio":
            # Clean audio bitrate (e.g., "256kbps" → "256")
            bitrate_clean = re.sub(r"\D", "", audio_bitrate)
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'quiet': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': bitrate_clean
                }]
            }
        else:
            res_map = {
                '144p': 'bestvideo[height<=144]+bestaudio/best',
                '360p': 'bestvideo[height<=360]+bestaudio/best',
                '480p': 'bestvideo[height<=480]+bestaudio/best',
                '720p': 'bestvideo[height<=720]+bestaudio/best',
                '1080p': 'bestvideo[height<=1080]+bestaudio/best'
            }
            ydl_opts = {
                'format': res_map.get(resolution, 'best'),
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'quiet': True,
                'merge_output_format': 'mp4'
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)
            if format_type == "audio":
                filename = os.path.splitext(filename)[0] + '.mp3'
            ydl.download([url])

            return filename, info.get('title', 'video')
    except Exception as e:
        st.error(f"❌ Error downloading: {str(e)}")
        return None, None

# Main App
url = st.text_input("🎯 Enter video URL:")

if url:
    with st.spinner("🔍 Fetching video details..."):
        video_info = get_video_info(url)

    if video_info:
        st.image(video_info['thumbnail'], width=400, use_container_width=True)
        st.subheader(video_info['title'])
        minutes, seconds = divmod(video_info['duration'], 60)
        st.write(f"⏱️ Duration: {int(minutes)}m {int(seconds)}s")

        download_type = st.radio("Download as:", ("Video", "Audio"))
        if download_type == "Video":
            resolution = st.selectbox("Select Resolution:", ["144p", "360p", "480p", "720p", "1080p"])
            format_type = "video"
            audio_bitrate = None
        else:
            resolution = None
            format_type = "audio"
            audio_bitrate = st.selectbox("Select Audio Bitrate:", ["132kbps", "256kbps", "320kbps"])

        if st.button("Download"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_text.text("Downloading...")

            for percent_complete in range(0, 100, 5):
                time.sleep(0.01)
                progress_bar.progress(percent_complete + 5)

            filename, title = download_video(url, format_type, resolution, audio_bitrate)

            if filename and os.path.exists(filename):
                progress_bar.empty()
                status_text.markdown('<p class="success-msg">✅ Download complete!</p>', unsafe_allow_html=True)
                with open(filename, "rb") as file:
                    st.download_button(
                        label="💾 Save to device",
                        data=file,
                        file_name=sanitize_filename(os.path.basename(filename)),
                        mime="audio/mp3" if format_type == "audio" else "video/mp4"
                    )
                try:
                    os.remove(filename)
                except:
                    pass
            else:
                st.error("Download failed. Please check the URL or try another resolution.")
