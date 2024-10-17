import os

# 텍스트 파일을 읽어서 정보를 파싱하는 함수
def parse_transcription_file(transcription_file_path):
    segments = []
    with open(transcription_file_path, 'r', encoding='utf-8') as file:
        segment = {}
        for line in file:
            line = line.strip()
            if line.startswith("File:"):
                if segment:  # 이전 구간이 있다면 추가
                    segments.append(segment)
                segment = {"file": line.split(": ")[1]}
            elif line.startswith("Time range:"):
                segment["time_range"] = line.split(": ")[1]
            elif line.startswith("Category:"):
                segment["category"] = line.split(": ")[1]
            elif line.startswith("Transcription:"):
                segment["transcription"] = ""
            else:
                if segment.get("transcription", None) is not None:
                    segment["transcription"] += line + " "
        
        # 마지막 세그먼트 추가
        if segment:
            segments.append(segment)
    
    return segments

# HTML 파일 생성 함수
def generate_html_from_transcription(transcription_file_path, audio_dir, output_html_path):
    segments = parse_transcription_file(transcription_file_path)

    with open(output_html_path, 'w', encoding='utf-8') as html_file:
        # HTML 기본 구조 작성
        html_file.write("""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Radio Program</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
        }
        h1, h2 {
            color: #333;
        }
        p {
            margin-bottom: 1em;
        }
        hr {
            margin: 2em 0;
        }
        .audio-container {
            margin-bottom: 1em;
        }
    </style>
</head>
<body>
    <h1>라디오 프로그램</h1>
""")

        # 각 세그먼트를 순차적으로 HTML에 추가
        for segment in segments:
            file_name = segment['file']
            time_range = segment['time_range']
            category = segment['category']
            transcription = segment.get('transcription', '').strip()
            audio_path = os.path.join(audio_dir, file_name)

            html_file.write(f"<h2>{category}</h2>\n")
            html_file.write(f"<p><strong>Time range:</strong> {time_range}</p>\n")
            html_file.write(f"<div class='audio-container'><audio controls><source src='{audio_path}' type='audio/mpeg'></audio></div>\n")

            # 대화인 경우에는 transcription을 출력, 음악인 경우에는 '음악'이라고 출력
            if category == "대화" and transcription:
                html_file.write(f"<p><strong>Transcription:</strong> {transcription}</p>\n")
            elif category == "음악":
                html_file.write(f"<p><strong>Transcription:</strong> 음악</p>\n")
            
            html_file.write("<hr>\n")

        # HTML 마무리
        html_file.write("""
</body>
</html>
""")

    print(f"HTML file created: {output_html_path}")

# 실행 예시
transcription_file_path = '/home/mh/homepage/transcriptions_sbs_power_test.txt'  # 텍스트 파일 경로
audio_dir = '/home/mh/homepage/output_segment/sbs_powerfm'  # 오디오 파일이 저장된 폴더
output_html_path = '/home/mh/homepage/transcriptions_sbspower.html'  # 생성할 HTML 파일 경로

generate_html_from_transcription(transcription_file_path, audio_dir, output_html_path)
