# 디맥갤 창작탭 이미지 크롤러

이 스크립트는 DCInside의 디맥갤(디제이맥스 리스펙트 V 갤러리) 창작탭에서 이미지를 자동으로 다운로드합니다.

## 설치 방법

1. Python 3.x가 설치되어 있어야 합니다.
2. Chrome 브라우저와 [ChromeDriver](https://chromedriver.chromium.org/downloads)가 필요합니다. (Chrome 버전에 맞는 드라이버를 설치 후, 환경변수에 추가하거나 실행 폴더에 두세요)
3. 필요한 패키지 설치:

```
pip install -r requirements.txt
```

## 사용법

```
python creation.py경로 --start 1 --end 10 --save_dir "이미지저장경로" --log "로그파일경로"
```

- `--start`: 시작 페이지 번호 (필수)
- `--end`: 끝 페이지 번호 (필수)
- `--save_dir`: 이미지 저장 경로 (필수)
- `--log`: 로그 파일 경로 (필수)

예시:

```
python C:\creation.py --start 1 --end 5 --save_dir "C:\사진저장폴더" --log "C:\사진저장폴더\크롤로그.txt"
```

> **주의:** `--save_dir`, `--log` 옵션을 반드시 입력해야 하며, 입력하지 않으면 실행되지 않습니다.

## 참고 사항
- GIF, 동영상 파일은 저장하지 않습니다.
- 게시글 제목이 파일명으로 사용됩니다.
- 중복 다운로드를 방지하기 위해 로그 파일을 사용합니다.
- 크롬드라이버가 시스템에 설치되어 있어야 합니다.
- 오직 디맥갤 창작탭만 지원합니다. 
