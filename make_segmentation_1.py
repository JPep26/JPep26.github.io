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

# 3. 'noEnergy' 구간을 다음 구간과 병합하고, 음악 구간을 3-5분 사이로 그룹화, speech 구간을 병합
def process_segments(segmentation):
    grouped_segments = []
    current_music = None
    current_speech = None

    for i, (label, start, end) in enumerate(segmentation):
        duration = end - start

        if label == 'noEnergy' and current_speech and (end - start) < 1:
            # noEnergy 구간이 1초 미만일 경우 무시하고 이전 구간과 병합
            if i + 1 < len(segmentation):
                next_label, next_start, next_end = segmentation[i + 1]
                if next_label == current_speech[0]:  # 이전 구간과 다음 구간이 동일한 label일 때 병합
                    current_speech[2] = next_end
                continue

        elif label == 'music' and duration <30:
            continue    
        elif label == 'noEnergy' and current_music:
            # noEnergy 구간을 이전 음악 구간에 병합
            current_music[2] = end
        elif label == 'music' and duration >= 60:
            # 음악 구간을 3-5분 사이로 그룹화
            if current_music and (end - current_music[1]) > 300:
                grouped_segments.append(current_music)
                current_music = None
            if current_music:
                current_music[2] = end
            else:
                current_music = ['music', start, end]
        elif label in ['male', 'female']:
            if current_speech and (start - current_speech[2]) <= 1:  # 1초 이하의 차이
                # 이전 speech 구간과 병합
                current_speech[2] = end
            else:
                if current_speech:
                    grouped_segments.append(current_speech)
                current_speech = [label, start, end]
        else:
            if current_speech:
                grouped_segments.append(current_speech)
                current_speech = None
            grouped_segments.append([label, start, end])

    if current_music and (current_music[2]-current_music[1])>=30:
        grouped_segments.append(current_music)
    if current_speech:
        grouped_segments.append(current_speech)

    return grouped_segments

# 4. 편성표 정보로 음악 구간을 보정
def correct_music_segments_with_playlist(segments, playlist_df):
    corrected_segments = []
    playlist_times = playlist_df['시작시간'].apply(time_to_seconds).tolist()

    for i, (label, start, end) in enumerate(segments):
        if label == 'music':
            matched=False
            for playlist_index, playlist_start_time in enumerate(playlist_times):
                if abs(start - playlist_start_time) < 60:  # 시작 시간이 60초 이내일 경우 보정
                    new_start = playlist_start_time
                    # 종료 시간은 다음 음악의 시작 시간 또는 원래 종료 시간
                    new_end = end
                    corrected_segments.append(['music', new_start, new_end])
                    matched=True
                    break
            if not matched:
                corrected_segments.append([label, start, end])
        else:
            corrected_segments.append([label, start, end])

    return corrected_segments

# 5. 병합된 구간을 저장하는 함수 (병합된 MP3 파일 생성)
def save_merged_segments(merged_segments, original_audio, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    merged_file_names = []

    for i, (label, start, end) in enumerate(merged_segments):
        start_ms = start * 1000  # 밀리초로 변환
        end_ms = end * 1000      # 밀리초로 변환

        # 구간 추출
        segment = original_audio[start_ms:end_ms]

        # 파일 이름 설정
        if label in ['male', 'female']:
            file_label = "speech_segment"
        else:
            file_label = label

        output_file_path = os.path.join(output_dir, f"{file_label}_merged_{i + 1}.mp3")

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
input_mp3_path = "/home/mh/Radio/sbs_powerfm/sbs_powerfm_20240924_2000.mp3"  # MP3 파일 경로를 실제 파일로 대체하세요
output_dir = "/home/mh/homepage/output_segment/sbs_powerfm/"  # 구간 파일이 저장될 디렉토리
output_text_file = os.path.join(output_dir, "segment_info.txt")  # 구간 정보를 저장할 텍스트 파일 경로

# 오디오 파일 세그멘테이션
segmentation, original_audio = segment_audio(input_mp3_path)

# 세그멘테이션 결과 처리 (noEnergy 병합 및 음악 구간 그룹화, speech 병합)
grouped_segments = process_segments(segmentation)

# 편성표 정보를 반영하여 구간 보정
corrected_segments = correct_music_segments_with_playlist(grouped_segments, playlist_df)

# 구간 병합 (1초 이하의 간격일 때)
merged_segments = correct_music_segments_with_playlist(corrected_segments, playlist_df)

# 병합된 구간을 파일로 저장
merged_file_names = save_merged_segments(merged_segments, original_audio, output_dir)

# 병합된 구간 정보 및 파일명을 텍스트 파일로 저장
save_segment_info_to_text(merged_file_names, output_text_file)

# 병합된 구간을 시간 형식으로 출력
for label, start, end, file_path in merged_file_names:
    start_time_str = str(timedelta(seconds=start))
    end_time_str = str(timedelta(seconds=end))
    print(f"{label}: {start_time_str} - {end_time_str}, File: {file_path}")