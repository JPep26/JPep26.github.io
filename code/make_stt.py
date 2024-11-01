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

# segment_info.txt에서 타임스탬프 정보를 읽는 함수
def load_segment_info(segment_info_path):
    segment_info = []
    with open(segment_info_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:  # 빈 줄 건너뛰기
                continue

            try:
                # "label: start_time - end_time" 형식에 맞게 split 수행
                label_time, time_range = line.split(": ", 1)
                start_time_str, end_time_str = time_range.split(" - ")
                segment_info.append((label_time, start_time_str, end_time_str))
            except ValueError:
                print(f"Warning: Line format incorrect, skipping line: {line}")
                continue  # 잘못된 형식의 라인은 건너뜀
    return segment_info

# 시간을 초로 변환하는 헬퍼 함수
def convert_time_to_seconds(time_str):
    t = list(map(float, time_str.split(":")))
    return int(t[0] * 3600 + t[1] * 60 + t[2])

# segment_info에서 세 가지 값 (label, start_time, end_time)을 unpack
def transcribe_by_timestamps(segment_info, audio_path, output_file, model):
    with open(output_file, 'w') as f:
        for label, start_time_str, end_time_str in segment_info:
            start_seconds = convert_time_to_seconds(start_time_str)
            end_seconds = convert_time_to_seconds(end_time_str)

            print(f"Transcribing {audio_path} from {start_time_str} to {end_time_str} ...")

            # Whisper 모델로 해당 시간 구간에서 텍스트 변환
            result = model.transcribe(audio_path, task='transcribe', initial_prompt=None, verbose=False,
                                      condition_on_previous_text=False)

            # 변환된 텍스트와 타임스탬프 기록
            segment_text = extract_segment_text(result, start_seconds, end_seconds)
            f.write(f"Time range: [{start_time_str} - {end_time_str}]\n")
            f.write("Transcription:\n")
            f.write(segment_text + "\n\n")
            print(f"Saved transcription for time range [{start_time_str} - {end_time_str}]")

            # 구간이 끝났다는 표시를 출력
            print(f"구간 종료: [{start_time_str} - {end_time_str}]\n")

# Whisper 결과에서 특정 구간 텍스트를 추출하는 함수
def extract_segment_text(result, start_seconds, end_seconds):
    segment_text = []
    for segment in result['segments']:
        # 구간의 시작/끝 시간이 타임스탬프 구간에 포함될 경우만 텍스트 추가
        if start_seconds <= segment['start'] < end_seconds:
            segment_text.append(segment['text'])
    return " ".join(segment_text)

# 전체 과정 실행
segment_info_path = "/home/dnlab/Whisper/seg/mbc_fm4u/segment1007_info.txt"  # segment_info.txt 파일 경로
audio_path = "/home/dnlab/Whisper/mbc_fm4u/mbc_fm4u_20241007_0200.mp3"  # MP3 파일 경로
output_file = "/home/dnlab/Whisper/text_result/mbc_1007_text.txt"  # 결과를 저장할 파일 경로

# Whisper 모델 로드
model = load_whisper_model()

if model:
    # 타임스탬프 정보 로드
    segment_info = load_segment_info(segment_info_path)

    # STT를 타임스탬프 구간에 맞게 처리하고, 결과를 파일에 저장
    transcribe_by_timestamps(segment_info, audio_path, output_file, model)
else:
    print("Failed to load Whisper model.")