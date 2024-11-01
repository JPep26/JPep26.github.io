import os
from openai import OpenAI
import re
import pandas as pd

# OpenAI API 키 설정
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))


# 선곡표 CSV 파일 로드
def load_spotify_data(file_path):
    return pd.read_csv(file_path)

# segment_info.txt 파일 읽기
def read_segment_info(file_path):
    segments = []
    with open(file_path, 'r') as file:
        for line in file:
            match = re.match(r".*?(\d+:\d+:\d+\.\d+) - (\d+:\d+:\d+\.\d+)", line)
            if match:
                start_time = match.group(1)
                end_time = match.group(2)
                segments.append({"start": start_time, "end": end_time})
    return segments

# STT 결과 파일 읽기
def read_stt_results(file_path):
    segments_text = {}
    with open(file_path, 'r') as file:
        current_time_range = None
        current_transcription = []

        for line in file:
            time_match = re.match(r"Time range: \[(\d+:\d+:\d+\.\d+) - (\d+:\d+:\d+\.\d+)\]", line)
            if time_match:
                # 저장된 구간이 있으면 추가
                if current_time_range:
                    segments_text[current_time_range] = "\n".join(current_transcription)
                
                # 새로운 구간 시작
                current_time_range = f"{time_match.group(1)} - {time_match.group(2)}"
                current_transcription = []

            elif line.startswith("Transcription:"):
                continue  # "Transcription:"이라는 라벨은 무시

            else:
                # 구간의 텍스트를 추가
                current_transcription.append(line.strip())

        # 마지막 구간 저장
        if current_time_range:
            segments_text[current_time_range] = "\n".join(current_transcription)

    return segments_text

# 시간 문자열을 초 단위로 변환하는 함수 (수정된 버전)
def time_to_seconds(time_str):
    h, m, s = re.split(':', time_str)
    s = float(s)  # 초 부분은 소수점까지 포함하여 변환
    return int(h) * 3600 + int(m) * 60 + s

# 구간에 곡을 할당하기 위한 함수
def assign_songs_to_segments(segments, songs):
    current_song_index = 0
    for segment in segments:
        segment_start = time_to_seconds(segment['start'])
        segment_end = time_to_seconds(segment['end'])
        segment_duration = segment_end - segment_start
        segment_songs = []

        while current_song_index < len(songs) and segment_duration > 0:
            song = songs[current_song_index]
            if segment_duration >= song['Duration (s)']:
                segment_songs.append(song)
                segment_duration -= song['Duration (s)']
                current_song_index += 1
            else:
                break

        segment["songs"] = segment_songs

# Chat-GPT API를 사용하여 긴 텍스트를 먼저 요약하는 함수
def summarize_long_text(long_text):
    prompt = f"""
    다음 텍스트를 간략히 요약해 주세요:
    {long_text}
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,  # max_tokens 값을 늘려서 더 많은 내용을 요약
        temperature=0.5
    )
    return response.choices[0].message.content.strip()

# 긴 텍스트를 여러 부분으로 나누어 요약하는 함수
def summarize_text_in_parts(long_text, max_tokens_per_part=3000):
    parts = [long_text[i:i + max_tokens_per_part] for i in range(0, len(long_text), max_tokens_per_part)]
    summarized_parts = [summarize_long_text(part) for part in parts]
    return " ".join(summarized_parts)

# Chat-GPT API를 사용하여 구간 정보 요약
def summarize_segment(segment, segment_text):
    # 최대 컨텍스트 길이를 초과하는 경우 긴 텍스트를 먼저 요약
    max_context_length = 8192
    if len(segment_text) > max_context_length:
        segment_text = summarize_text_in_parts(segment_text)

    prompt = f"""
    다음 텍스트를 '주요 내용', '청취자 사연', '음악 소개', '광고 정보'로 나누어서 각 항목의 내용을 출력해 주세요:
    {segment_text}

    포함된 음악 목록:
    {', '.join([f"'음악제목': {song['Track Name']}, '가수': {song['Artists']}" for song in segment['songs']])}

    형식:
    주요 내용:
    - (내용)

    청취자 사연:
    - (내용)

    음악 소개:
    -  제목: (곡 제목)
       가수: (가수 이름)
       설명: (곡 설명)

    광고 정보:
    - (내용)
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,  # max_tokens 값을 늘려서 더 많은 내용을 생성
        temperature=0.5
    )
    return response.choices[0].message.content.strip()



# 파일 경로 설정
spotify_csv_path = '/home/dnlab/Whisper/csv/spotify_song_info_0926.csv'
segment_info_path = '/home/dnlab/Whisper/seg/mbc_fm4u/segment_0926_info.txt'
stt_results_path = '/home/dnlab/Whisper/text_result/mbc_0926_text.txt'
output_summary_path = '/home/dnlab/Whisper/gpt_result/segment_summaries_0926_ver5.txt'

# 데이터 로드
spotify_data = load_spotify_data(spotify_csv_path)
segments = read_segment_info(segment_info_path)
stt_results = read_stt_results(stt_results_path)

# 곡 정보를 구간에 할당
assign_songs_to_segments(segments, spotify_data.to_dict(orient='records'))

# 각 구간에 대해 요약 진행 및 파일로 저장
with open(output_summary_path, 'w') as output_file:
    for segment in segments:
        segment_key = f"{segment['start']} - {segment['end']}"
        segment_text = stt_results.get(segment_key, "해당 구간의 STT 텍스트가 없습니다.")
        try:
            summary = summarize_segment(segment, segment_text)
            output_file.write(f"구간 ({segment['start']} - {segment['end']}) 요약:\n")
            output_file.write(summary + "\n\n" + "-"*50 + "\n\n")
        except Exception as e:
            output_file.write(f"구간 ({segment['start']} - {segment['end']})에서 오류 발생: {str(e)}\n\n" + "-"*50 + "\n\n")

print(f"요약 결과가 '{output_summary_path}' 파일로 저장되었습니다.")
