import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL 설정
url = "https://www.imbc.com/broad/radio/fm4u/moviemusic/musictable/index.html"

# User-Agent 설정으로 웹사이트의 접근 허용 요청
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
}

# 웹 페이지 요청 및 HTML 파싱
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# 데이터를 저장할 리스트 초기화
song_data = []

# 선곡표 정보를 담고 있는 tbody 태그 선택
tbody = soup.find('tbody')
if tbody:
    # 각 tr 태그 순회
    for tr in tbody.find_all('tr'):
        # 파트 정보가 있는 행 확인
        if 'part' in tr.get('class', []):
            part_name = tr.get_text(strip=True)
        else:
            # 곡 정보 행에서 데이터 추출
            tds = tr.find_all('td')
            if len(tds) >= 3:
                number = tds[0].get_text(strip=True)
                title = tds[1].get_text(strip=True)
                singer = tds[2].get_text(strip=True)
                song_data.append([part_name, number, title, singer])

# DataFrame으로 변환 후 CSV 파일로 저장
df = pd.DataFrame(song_data, columns=['파트', '번호', '제목', '가수'])
df.to_csv('songlist.csv', index=False, encoding='utf-8-sig')

print("크롤링 완료: songlist.csv 파일로 저장되었습니다.")
