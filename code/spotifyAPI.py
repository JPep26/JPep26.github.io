import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Spotify API 인증 설정
client_id = ''
client_secret = ''

client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# 크롤링한 선곡표 데이터 로드
data = [
    ["0926", "Radiation Ruling the Nation (based on \"Protection\")", "Massive Attack, Mad Professor"],
    ["0926", "Sunday Never Comes", "Ethan Hawke"],
    ["0926", "I'm Nuthin'", "Ethan Hawke"],
    ["0926", "All I Want To Do Is Rock", "Travis"],
    ["0926", "I Put A Spell On You", "Marilyn Manson"],
    ["0926", "청년폭도맹진가", "노브레인 (NoBrain)"],
    ["0926", "힘을 내세요", "이찬원"],
    ["0926", "That's Life", "Frank Sinatra"],
    ["0926", "Merry-Go-Round (from 'Howl's Moving Castle')", "Hisaishi Joe"],
    ["0926", "천취일생 (淺醉一生, Qian Zui Yi Sheng)", "엽천문"],
    ["0926", "야반가성 夜半歌聲", "장국영"]
]

# 곡 정보 검색 함수
def search_song(title, artist):
    query = f"track:{title} artist:{artist}"
    results = sp.search(q=query, type='track', limit=1)
    if results['tracks']['items']:
        track = results['tracks']['items'][0]
        return {
            'Track Name': track['name'],
            'Artists': ', '.join([artist['name'] for artist in track['artists']]),
            'Album': track['album']['name'],
            'Release Date': track['album']['release_date'],
            'Duration (s)': track['duration_ms'] / 1000  # 밀리초를 초로 변환
        }
    else:
        return None

# 각 곡에 대해 Spotify 정보 검색
song_info_list = []
for entry in data:
    date, title, artists = entry
    artist_list = artists.split(", ")
    song_info = search_song(title, artist_list[0])  # 첫 번째 아티스트를 기준으로 검색
    if song_info:
        song_info['Date'] = date
        song_info_list.append(song_info)

# DataFrame으로 변환 후 CSV 파일로 저장
df = pd.DataFrame(song_info_list)
df.to_csv('/home/dnlab/Whisper/csv/spotify_song_info_0926.csv', index=False, encoding='utf-8-sig')

print("Spotify 곡 정보가 'spotify_song_info.csv' 파일로 저장되었습니다.")
