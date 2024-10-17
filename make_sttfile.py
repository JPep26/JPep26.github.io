import os
import whisper
from datetime import timedelta

# Whisper 모델 로드 (GPU를 사용할 수 없으면 CPU로 자동 전환)
def load_whisper_model():
    try:
        model = whisper.load_model("medium")
    except Exception as e:
        print(f"Error loading Whisper model: {e}")
        model = None
    return model

# segment_info.txt에서 파일명과 타임스탬프 정보를 읽는 함수
def load_segment_info(segment_info_path):
    segment_info = {}
    with open(segment_info_path, 'r') as f:
        for line in f:
            # 라인의 형식은 "label: start_time - end_time, File: file_path" 형식임
            label_time, file_path = line.strip().split(", File: ")
            label, time_range = label_time.split(": ")
            start_time_str, end_time_str = time_range.split(" - ")
            segment_info[file_path] = (start_time_str, end_time_str)
    return segment_info

# 파일 이름에서 숫자를 추출하는 함수 (정렬을 위해 필요)
def extract_segment_number(file_name):
    base_name = os.path.splitext(file_name)[0]  # "speech_segment_24" -> "speech_segment_24"
    segment_number = base_name.split("_")[-1]  # "speech_segment_24" -> "24"
    return int(segment_number)  # "24" -> 24 (숫자형으로 변환)

# 카테고리를 파일 이름에 따라 설정하는 함수
def determine_category(file_name):
    if file_name.startswith("speech"):
        return "주제"
    elif file_name.startswith("music_merged"):
        return "음악"
    else:
        return None  # 해당하지 않는 경우 카테고리를 None으로 설정

# 모든 speech_segment 파일들을 Whisper로 변환하고, 결과를 하나의 텍스트 파일에 저장
def transcribe_speech_segments_to_single_file(segment_info_path, speech_dir, output_file, model):
    # segment_info.txt 파일에서 타임스탬프 정보 로드
    segment_info = load_segment_info(segment_info_path)

    # 디렉토리 내의 파일 목록을 숫자 순서대로 정렬
    audio_files = [f for f in os.listdir(speech_dir) if (f.startswith("speech")or f.startswith("music_merged")) and f.endswith(".mp3")]
    audio_files = sorted(audio_files, key=extract_segment_number)

    # 변환된 내용을 하나의 파일에 기록하기 위해 파일을 엶
    with open(output_file, 'w') as f:
        # 정렬된 speech_segment_*.mp3 파일들에 대해 변환 작업 수행
        for file_name in audio_files:
            category = determine_category(file_name)  # 카테고리 결정

            # 타임스탬프 정보를 가져옴
            speech_file_path = os.path.join(speech_dir, file_name)
            timestamp = segment_info.get(speech_file_path, None)

            if timestamp:
                start_time, end_time = timestamp

                if category == "주제":
                    # Whisper로 음성 파일을 텍스트로 변환
                    print(f"Transcribing {file_name} ...")
                    result = model.transcribe(speech_file_path)

                    # 타임스탬프와 함께 저장
                    f.write(f"File: {file_name}\n")
                    f.write(f"Time range: [{start_time} - {end_time}]\n")
                    f.write(f"Category: {category}\n")  # 카테고리 추가
                    f.write("Transcription:\n")
                    f.write(result['text'] + "\n\n")
                    print(f"Saved transcription for {file_name} with category {category} to {output_file}")

                elif category == "음악":
                    # 음악 파일은 변환을 하지 않고 타임스탬프와 카테고리만 기록
                    f.write(f"File: {file_name}\n")
                    f.write(f"Time range: [{start_time} - {end_time}]\n")
                    f.write(f"Category: {category}\n")
                    f.write("Transcription: \n\n")
                    print(f"Skipped transcription for music file {file_name}, saved time range and category only.")

                else:
                    print(f"Skipping non-speech or non-music file: {file_name}")
            else:
                print(f"Timestamp not found for {file_name}.")

# 전체 과정 실행
segment_info_path = "/home/mh/homepage/audio/korean_music/segment_info.txt"  # segment_info.txt 파일 경로
speech_dir = "/home/mh/homepage/audio/korean_music"  # speech_segment 파일들이 저장된 디렉토리
output_file = "/home/mh/homepage/text_result/korean_music.txt"  # 모든 변환된 텍스트를 하나의 파일에 저장

# Whisper 모델 로드
model = load_whisper_model()

if model:
    # 음성 파일을 변환하고 모든 결과를 하나의 텍스트 파일에 저장
    transcribe_speech_segments_to_single_file(segment_info_path, speech_dir, output_file, model)
else:
    print("Failed to load Whisper model.")
