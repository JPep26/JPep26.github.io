def parse_text_file(input_file):
    segments = []
    with open(input_file, 'r', encoding='utf-8') as file:
        segment = {}
        for line in file:
            line = line.strip()
            if line.startswith("File:"):
                if segment:
                    segments.append(segment)
                    segment = {}
                segment['file'] = line.replace("File:", "").strip()
            elif line.startswith("Time range:"):
                segment['time_range'] = line.replace("Time range:", "").strip()
            elif line.startswith("Category:"):
                segment['category'] = line.replace("Category:", "").strip()
            elif line.startswith("Transcription:"):
                segment['transcription'] = ""
            elif line:
                if 'transcription' in segment:
                    segment['transcription'] += line + " "
        if segment:
            segments.append(segment)
    return segments


def generate_html_from_segments(segments, output_file):
    html_template = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Radio Program</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
            }}
            h1, h2 {{
                color: #333;
            }}
            p {{
                margin-bottom: 1em;
            }}
            hr {{
                margin: 2em 0;
            }}
            .audio-container {{
                margin-bottom: 1em;
            }}
        </style>
    </head>
    <body>
        <h1>라디오 프로그램</h1>
        {segments}
    </body>
    </html>
    """

    segment_template = """
    <h2>{category}</h2>
    <p><strong>Time range:</strong> {time_range}</p>
    <div class='audio-container'><audio controls><source src='/home/mh/homepage/output_segments/{file}' type='audio/mpeg'></audio></div>
    <p><strong>Transcription:</strong> {transcription}</p>
    <hr>
    """

    segments_html = ""
    for entry in segments:
        segments_html += segment_template.format(
            category=entry["category"],
            time_range=entry["time_range"],
            file=entry["file"],
            transcription=entry["transcription"].strip()  # Transcription에서 끝에 공백 제거
        )

    html_content = html_template.format(segments=segments_html)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML 파일 '{output_file}'이 생성되었습니다.")


# Main function to execute the conversion
def convert_text_to_html(input_file, output_file):
    segments = parse_text_file(input_file)
    generate_html_from_segments(segments, output_file)


# 예시 실행
input_file = '/home/mh/homepage/transcriptions_kbs_test.txt' # 입력 텍스트 파일 경로
output_file = '/home/mh/homepage/transcriptions_kbs.html'  # 출력 HTML 파일 경로
convert_text_to_html(input_file, output_file)
