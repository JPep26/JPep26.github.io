import os
from inaSpeechSegmenter import Segmenter
from pydub import AudioSegment
from datetime import datetime, timedelta
import pandas as pd

# 1. 편성표 CSV 파일 로드
csv_file_path = '/home/mh/Radio/web_crawling_csv/kbs3_music_info_0926.csv'
playlist_df = pd.read_csv(csv_file_path)

# 시간 문자열을 초 단위로 변환하는 헬퍼 함수
def time_to_seconds(time_str):
    t = datetime.strptime(time_str, '%H:%M')
    return t.hour * 3600 + t.minute * 60

# 2. MP3 파일을 음성/음악/무음 구간으로 세그멘테이션
def segment_audio(input_mp3_path):
    # MP3 파일을 WAV로 변환
    audio = AudioSegment.from_mp3(input_mp3_path)
    wav_path = input_mp3_path.replace(".mp3", ".wav")
    audio.export(wav_path, format="wav")
   
    # inaSpeechSegmenter 모델 로드 및 세그멘테이션 실행
    seg = Segmenter()
    segmentation = seg(wav_path)
   
    return segmentation, audio

# 3. noEnergy를 다른 구간과 병합하고, speech와 music으로 분류하며, 60초 이상의 music을 기준으로 구간을 분리
def process_segments(segmentation):
    grouped_segments = []
    current_label = 'speech'
    current_start = None
    accumulated_duration = 0

    for i, (label, start, end) in enumerate(segmentation):
        duration = end - start

        if label == 'noEnergy':
            # 'noEnergy'는 무시하고 다음 구간과 병합 준비
            continue
        elif label in ['male', 'female']:
            label = 'speech'  # 'male', 'female'은 모두 'speech'로 통합

        if label == 'music' and duration >= 60:
            # 음악이 60초 이상일 때는 이전 구간까지 묶어서 저장하고, music 구간을 새로 시작
            if current_start is not None:
                grouped_segments.append([current_label, current_start, start])  # 이전 구간을 묶어서 저장
            grouped_segments.append(['music', start, end])  # 긴 music 구간을 추가
            current_label = 'speech'  # 다음 구간은 speech로 시작
            current_start = None
        else:
            # 현재 구간이 시작되지 않았다면 시작 시간을 설정
            if current_start is None:
                current_start = start
            accumulated_duration += duration

    # 마지막 구간 처리
    if current_start is not None:
        grouped_segments.append([current_label, current_start, end])

    return grouped_segments

# 4. 편성표 정보로 음악 구간을 보정
def correct_music_segments_with_playlist(segments, playlist_df):
    corrected_segments = []
    playlist_times = playlist_df['시작시간'].apply(time_to_seconds).tolist()

    for i, (label, start, end) in enumerate(segments):
        if label == 'music':
            matched = False
            for playlist_index, playlist_start_time in enumerate(playlist_times):
                if abs(start - playlist_start_time) < 60:  # 시작 시간이 60초 이내일 경우 보정
                    new_start = playlist_start_time
                    new_end = end
                    corrected_segments.append(['music', new_start, new_end])
                    matched = True
                    break
            if not matched:
                corrected_segments.append([label, start, end])
        else:
            corrected_segments.append([label, start, end])

    return corrected_segments

# 5. 병합된 구간을 저장하는 함수 (병합된 MP3 파일 생성, 음악은 60초 이상만 저장)
def save_merged_segments(merged_segments, original_audio, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    merged_file_names = []

    for i, (label, start, end) in enumerate(merged_segments):
        duration = end - start
        if label == 'music' and duration < 60:
            # 음악 구간이 60초 미만이면 저장하지 않음
            continue

        start_ms = start * 1000  # 밀리초로 변환
        end_ms = end * 1000      # 밀리초로 변환

        # 구간 추출
        segment = original_audio[start_ms:end_ms]

        output_file_path = os.path.join(output_dir, f"{label}_merged_{i + 1}.mp3")

        # 추출한 구간을 MP3 파일로 저장
        segment.export(output_file_path, format="mp3")
        print(f"Saved merged segment: {output_file_path}")
       
        # 파일명과 구간 정보를 함께 리스트에 저장
        merged_file_names.append((label, start, end, output_file_path))

    return merged_file_names

# 6. 구간 정보들과 파일명을 텍스트 파일에 저장하는 함수 추가
def save_segment_info_to_text(segment_file_names, output_file_path):
    with open(output_file_path, 'w') as f:
        for label, start, end, file_path in segment_file_names:
            start_time_str = str(timedelta(seconds=start))
            end_time_str = str(timedelta(seconds=end))
            f.write(f"{label}: {start_time_str} - {end_time_str}, File: {file_path}\n")
    print(f"Saved segment information with file names to: {output_file_path}")

# 7. 전체 과정 실행
input_mp3_path = "/home/mh/Radio/kbs_3radio/kbs_3radio_20240925_0600.mp3"  # MP3 파일 경로를 실제 파일로 대체하세요
output_dir = "/home/mh/homepage/test/"  # 구간 파일이 저장될 디렉토리
output_text_file = os.path.join(output_dir, "segment_info.txt")  # 구간 정보를 저장할 텍스트 파일 경로

# 오디오 파일 세그멘테이션
segmentation, original_audio = segment_audio(input_mp3_path)

# 세그멘테이션 결과 처리 (noEnergy 병합, speech와 music 구분, 음악 60초 이상에서만 구간 분리)
grouped_segments = process_segments(segmentation)

# 편성표 정보를 반영하여 구간 보정
corrected_segments = correct_music_segments_with_playlist(grouped_segments, playlist_df)

# 병합된 구간을 파일로 저장 (음악은 60초 이상일 때만 저장)
merged_file_names = save_merged_segments(corrected_segments, original_audio, output_dir)

# 병합된 구간 정보 및 파일명을 텍스트 파일로 저장
save_segment_info_to_text(merged_file_names, output_text_file)

# 병합된 구간을 시간 형식으로 출력
for label, start, end, file_path in merged_file_names:
    start_time_str = str(timedelta(seconds=start))
    end_time_str = str(timedelta(seconds=end))
    print(f"{label}: {start_time_str} - {end_time_str}, File: {file_path}")
