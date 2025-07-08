import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import shutil
import argparse
import sys

# 디맥갤 창작탭 URL 고정
BASE_URL = 'https://gall.dcinside.com/mgallery/board/lists/?id=djmaxrespect&search_head=30'

# 저장할 폴더
save_dir = r'C:\Users\chldm\Desktop\creation\djmax_photos'
os.makedirs(save_dir, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0'
}

def clean_filename(name):
    # 특수문자 제거
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    # 끝의 마침표, 공백 제거
    name = name.rstrip(' .')
    # 폴더명/파일명이 비어있으면 대체
    if not name:
        name = 'untitled'
    return name

def get_post_links(page=1):
    url = f"{BASE_URL}&page={page}"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    links = []
    for tr in soup.select('tr.ub-content.us-post'):
        for a in tr.select('a'):
            href = a.get('href', '')
            href_str = str(href) if href is not None else ''
            if href_str.startswith('/board/view/') or href_str.startswith('/mgallery/board/view/'):
                post_url = 'https://gall.dcinside.com' + href_str
                links.append(post_url)
                break  # 한 tr에서 하나만
    return links

def get_media_urls_with_driver(post_url, driver):
    driver.get(post_url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    # 제목 추출
    title_tag = soup.select_one('span.title_subject')
    title = title_tag.get_text(strip=True) if title_tag else 'no_title'
    safe_title = clean_filename(title)
    # 이미지, gif, 영상 추출
    img_tags = soup.select('div.imgwrap img')
    video_tags = soup.select('div.imgwrap video')
    source_tags = soup.select('div.imgwrap source')
    media_urls = []
    for tag in img_tags + video_tags + source_tags:
        src = tag.get('src')
        src_str = str(src) if src is not None else ''
        if src_str.startswith('http') or src_str.startswith('//'):
            media_urls.append(src_str)
    media_urls = list(dict.fromkeys(media_urls))
    return media_urls, safe_title

def download_media(url, save_dir, base_filename, idx, logf):
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            ext = url.split('.')[-1].split('?')[0].lower()
            # gif, mp4, webm만 건너뛰고 나머지는 모두 jpg로 저장
            if ext in ['gif', 'mp4', 'webm']:
                print(f"    건너뜀(이미지 아님): {url}")
                return True
            if ext not in ['jpg', 'jpeg', 'png']:
                ext = 'jpg'
            filename = f"{base_filename}_{idx+1}.{ext}"
            path = os.path.join(save_dir, filename)
            if os.path.exists(path):
                print(f"이미 존재: {filename} (건너뜀)")
                return True
            media_headers = {
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://gall.dcinside.com/'
            }
            res = requests.get(url, headers=media_headers, timeout=5)
            if res.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(res.content)
                print(f"    저장 완료: {filename}")
                return True
            else:
                print(f"    저장 실패(응답코드): {filename} (시도 {attempt}/{max_retries})")
        except Exception as e:
            print(f"    저장 실패(에러): {filename} - {e} (시도 {attempt}/{max_retries})")
        if attempt < max_retries:
            print(f"    재시도 중... ({attempt+1}/{max_retries})")
    return False

def process_post(post_url, save_dir, logf, processed_ids):
    # 각 스레드마다 드라이버 생성
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920x1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0')
    driver = webdriver.Chrome(options=chrome_options)
    try:
        # 게시글 id 추출
        parsed = urlparse(post_url)
        qs = parse_qs(parsed.query)
        post_id = qs.get('no', ['unknown'])[0]
        if post_id in processed_ids:
            print(f"  게시글 {post_url} (이미 처리됨, 건너뜀)")
            return
        print(f"  게시글 {post_url}")
        media_urls, safe_title = get_media_urls_with_driver(post_url, driver)
        if media_urls:
            for img_idx, media_url in enumerate(media_urls):
                download_media(media_url, save_dir, safe_title, img_idx, logf)
        else:
            print("    (미디어 없음)")
        logf.write(f"{post_id}\n")
        logf.flush()
    finally:
        driver.quit()

def main():
    parser = argparse.ArgumentParser(description='디맥갤 창작탭 이미지 크롤러')
    parser.add_argument('--start', type=int, required=True, help='다운로드 시작 페이지 번호')
    parser.add_argument('--end', type=int, required=True, help='다운로드 끝 페이지 번호')
    parser.add_argument('--save_dir', type=str, required=True, help='이미지 저장 폴더(필수)')
    parser.add_argument('--log', type=str, required=True, help='로그 파일 경로(필수)')
    args = parser.parse_args()

    save_dir = os.path.abspath(args.save_dir)
    os.makedirs(save_dir, exist_ok=True)
    log_path = os.path.abspath(args.log)

    total_success = 0
    total_fail = 0
    start_time = time.time()

    processed_ids = set()
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as logf:
            for line in logf:
                processed_ids.add(line.strip())

    with open(log_path, 'a', encoding='utf-8') as logf:
        try:
            batch_size = 10
            for batch_start in range(args.start, args.end + 1, batch_size):
                batch_end = min(batch_start + batch_size - 1, args.end)
                print(f"\n===== {batch_start}~{batch_end} 페이지 크롤링 중 =====")
                post_urls = []
                for page in range(batch_start, batch_end + 1):
                    print(f"  - {page}페이지 게시글 수집")
                    post_links = get_post_links(page=page)
                    post_urls.extend(post_links)
                # 이미 처리된 게시글 거르기
                submit_urls = []
                for post_url in post_urls:
                    parsed = urlparse(post_url)
                    qs = parse_qs(parsed.query)
                    post_id = qs.get('no', ['unknown'])[0]
                    if post_id in processed_ids:
                        print(f"  게시글 {post_url} (이미 처리됨, 건너뜀)")
                        continue
                    submit_urls.append(post_url)
                # 병렬 다운로드
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [
                        executor.submit(process_post, post_url, save_dir, logf, processed_ids)
                        for post_url in submit_urls
                    ]
                    for future in as_completed(futures):
                        pass
        except KeyboardInterrupt:
            print('\nCtrl+C로 크롤링이 중단되었습니다.')
        except Exception as e:
            print(f"오류 발생: {e}")
        finally:
            end_time = time.time()
            print(f"\n모든 미디어 다운로드 완료!")
            print(f"소요 시간: {end_time - start_time:.2f}초")
            print("드라이버 종료!")

if __name__ == '__main__':
    main()
