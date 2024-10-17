import os

# 요약된 텍스트 파일을 읽는 함수
def read_summary_file(file_path):
    summaries = []
    with open(file_path, 'r', encoding='utf-8') as f:
        block = {}
        for line in f:
            if line.startswith("Time range:"):
                if block:  # 이전 block이 있으면 저장
                    summaries.append(block)
                    block = {}
                block['time_range'] = line.split("Time range: ")[1].strip()
            elif line.startswith("Summary:"):
                block['summary'] = line.split("Summary: ")[1].strip()
        if block:  # 마지막 block 추가
            summaries.append(block)
    return summaries

# 요약 전 텍스트 파일에서 Time range에 맞는 파일을 찾는 함수
def find_audio_file(time_range, full_transcription_file):
    with open(full_transcription_file, 'r', encoding='utf-8') as f:
        blocks = f.read().split("\n\n")
        for block in blocks:
            if "Time range" in block and time_range in block:
                lines = block.split("\n")
                for line in lines:
                    if line.startswith("File:"):
                        audio_file = line.split("File: ")[1].strip()
                        return audio_file
    return None

# HTML 생성 함수 (상대 경로 설정)
def generate_html(summary_data, audio_dir, output_html):
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Audio Summary</title>
    </head>
    <body>
        <h1>Audio Summary</h1>
    """
    
    for item in summary_data:
        time_range = item['time_range']
        summary = item['summary']

        # 오디오 파일 찾기
        audio_file = find_audio_file(time_range, full_transcription_file)
        if audio_file:
            # 오디오 파일의 상대 경로 설정
            relative_audio_path = os.path.relpath(os.path.join(audio_dir, audio_file), os.path.dirname(output_html))

            # HTML 요소로 추가 (오디오 파일과 요약 텍스트)
            html_content += f"""
            <div>
                <h2>Time range: {time_range}</h2>
                <p>Summary: {summary}</p>
                <audio controls>
                    <source src="{relative_audio_path}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
            </div>
            <hr>
            """
        else:
            html_content += f"""
            <div>
                <h2>Time range: {time_range}</h2>
                <p>Summary: {summary}</p>
                <p><strong>Audio file not found for this time range.</strong></p>
            </div>
            <hr>
            """
    
    # HTML 종료 태그 추가
    html_content += """
    </body>
    </html>
    """

    # HTML 파일로 저장
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"HTML 파일이 {output_html}로 생성되었습니다.")

# 텍스트 파일을 읽어오는 함수
def read_transcription_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 전체 과정 실행
summary_file = "summary/tbc_dreamfm_summary.txt"  # 요약된 텍스트 파일 경로
full_transcription_file = "text_result/tbc_dreamfm.txt"  # 요약 전 텍스트 파일 경로
audio_dir = "audio/tbc_dreamfm"  # 오디오 파일들이 저장된 디렉토리
output_html = "html/tbc_dreamfm.html"  # HTML 결과 파일 경로

# 요약된 텍스트 파일에서 데이터 읽기
summary_data = read_summary_file(summary_file)

# HTML 생성 작업 실행
generate_html(summary_data, audio_dir, output_html)
