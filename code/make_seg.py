import os
from inaSpeechSegmenter import Segmenter
from pydub import AudioSegment
from datetime import datetime, timedelta
import pandas as pd

# 1. 편성표 CSV 파일 로드
csv_file_path = '/home/dnlab/Whisper/csv/kbs3_music_info_0926.csv'
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
   
    return segmentation

# 3. noEnergy를 다른 구간과 병합하고, 긴 음악 구간(60초 이상)과 그 직전 구간을 묶어서 저장
def process_segments(segmentation):
    grouped_segments = []
    current_label = 'speech'
    current_start = None
    accumulated_duration = 0  # 누적된 구간의 길이

    for i, (label, start, end) in enumerate(segmentation):
        duration = end - start

        # male, female을 speech로 통합
        if label in ['male', 'female']:
            label = 'speech'

        # 긴 음악 구간(60초 이상)을 만나면 그 직전 구간을 함께 묶어서 저장
        if label == 'music' and duration >= 60:
            if current_start is not None:
                # 직전의 speech/noEnergy 구간과 현재 music 구간을 묶어서 저장
                grouped_segments.append(['speech_music_combined', current_start, end])
            else:
                # 만약 시작 시간이 없으면(첫 구간이 음악일 때), 음악 구간만 저장
                grouped_segments.append([label, start, end])
            current_label = 'speech'  # 다음은 speech로 시작
            current_start = None
            accumulated_duration = 0  # 누적 초기화
        else:
            # noEnergy, speech는 병합하여 처리
            if current_start is None:
                current_start = start  # 시작 시간을 설정
                current_label = label  # 현재 라벨을 설정
            else:
                current_label = 'speech' if label == 'speech' or label == 'noEnergy' else label

            accumulated_duration += duration
            current_start = min(current_start, start)  # 시작 시간을 유지

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

# 5. 구간 정보들을 텍스트 파일에 저장하는 함수 (음성 파일은 저장하지 않음)
def save_segment_info_to_text(segment_file_names, output_file_path):
    with open(output_file_path, 'w') as f:
        for label, start, end in segment_file_names:
            start_time_str = str(timedelta(seconds=start))
            end_time_str = str(timedelta(seconds=end))
            f.write(f"{label}: {start_time_str} - {end_time_str}\n")
    print(f"Saved segment information to: {output_file_path}")

# 편성표 CSV 파일 로드
playlist_df = pd.read_csv(csv_file_path)

input_mp3_path = "/home/dnlab/Whisper/mbc_fm4u/mbc_fm4u_20241008_0200.mp3"  # MP3 파일 경로를 실제 파일로 대체하세요
output_dir = "/home/dnlab/Whisper/seg/mbc_fm4u"  # 구간 파일이 저장될 디렉토리
output_text_file = os.path.join(output_dir, "segment1008_info.txt")  # 구간 정보를 저장할 텍스트 파일 경로

# 오디오 파일 세그멘테이션
segmentation = segment_audio(input_mp3_path)

# 세그멘테이션 결과 처리 (noEnergy 병합, speech와 music 구분, 음악 60초 이상에서만 구간 분리)
grouped_segments = process_segments(segmentation)

# 편성표 정보를 반영하여 구간 보정
corrected_segments = correct_music_segments_with_playlist(grouped_segments, playlist_df)

# 구간 정보만 텍스트 파일에 저장
save_segment_info_to_text(corrected_segments, output_text_file)

# 병합된 구간을 시간 형식으로 출력
for label, start, end in corrected_segments:
    start_time_str = str(timedelta(seconds=start))
    end_time_str = str(timedelta(seconds=end))
    print(f"{label}: {start_time_str} - {end_time_str}")
