import json
import os

def generate_html(segment_data, audio_file_path):
    audio_file_url = os.path.basename(audio_file_path)
    html = """
    <html><head>
        <title>Radio Broadcast</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.4; margin: 20px; font-size: 14px; }}
            header {{ text-align: center; margin-bottom: 40px; }}
            h1 {{ font-size: 28px; font-weight: bold; }}
            h2 {{ font-size: 20px; }}
            h3 {{ font-size: 16px; }}
            section {{ margin-bottom: 40px; }}
            footer {{ text-align: center; margin-top: 40px; }}
            .play-button {{ cursor: pointer; color: blue; text-decoration: underline; }}
        </style>
        <script>
            function playAudio(start, end) {{
                var audio = document.getElementById('audioPlayer');
                audio.currentTime = start;
                audio.play();
                if (end) {{
                    setTimeout(function() {{
                        audio.pause();
                    }}, (end - start) * 1000);
                }}
            }}
        </script>
    </head><body>
    <header>
        <h1>Radio Broadcast</h1>
    </header>

    <!-- MP3 Audio Player -->
    <audio id="audioPlayer" controls="">
        <source src="{}" type="audio/mpeg">
        Your browser does not support the audio element.
    </audio>
    <br><br>
    """.format(audio_file_url)

    for segment in segment_data:
        start = segment["start"]
        end = segment["end"]
        summary = segment["summary"].replace('\n', '<br>')
        html += """
        <section>
            <h2><span class="play-button" onclick="playAudio({}, {})">[{} - {}]</span></h2>
            <h3>Summary</h3>
            <p style="white-space: pre-wrap;">{}</p>
        </section>
        """.format(start, end, start, end, summary)

    html += """
    <footer>
        <p>Generated automatically from radio script.</p>
    </footer>
    </body></html>
    """

    return html

def parse_time(time_str):
    h, m, s = time_str.split(":")
    s, ms = s.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 100000

# Load segment data from text file
segment_file_path = "/home/dnlab/Whisper/gpt_result/segment_summaries_0925_ver5.txt"
segment_data = []
with open(segment_file_path, "r", encoding="utf-8") as f:
    content = f.read()
    segments = content.split("--------------------------------------------------\n")
    for segment in segments:
        lines = segment.strip().split("\n")
        if len(lines) > 1:
            time_range = lines[0].split(" - ")
            start = time_range[0].split("(")[1].strip()
            end = time_range[1].split(")")[0].strip()
            summary = "\n".join(lines[1:]).strip()
            segment_data.append({"start": parse_time(start), "end": parse_time(end), "summary": summary})



# Load audio file from local path
audio_file_path = "/home/dnlab/Whisper/mbc_fm4u/mbc_fm4u_20240925_0200.mp3"
html_output = generate_html(segment_data, audio_file_path)

# Save to file
os.makedirs(os.path.dirname("/home/dnlab/Whisper/html/output_0925.html"), exist_ok=True)
with open("/home/dnlab/Whisper/html/output_0925.html", "w", encoding="utf-8") as f:
    f.write(html_output)
