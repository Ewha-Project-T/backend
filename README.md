#Ewha Language Translation Platform
---

## 필요 모듈 설치

```python
pip install -r requirements.txt
```

## 디렉토리 구성

아무것도 안써져있는 파일들도 다 필요합니다. 삭제하지마세요.

```
root
ㄴ docs : API docs 관련 문서. API 제작 후, `@swag_from` 으로 경로명시 해줄 것.
ㄴ server : 서버 관련한 파일들이 존재. 코딩해야할 곳
    ㄴ apis : API 코드들이 모여있는곳
    ㄴ (추후 문서 파싱이라던지 여러 작업들을 따로 빼놓을 디렉토리를 구상하여 깔끔하게 정돈해주세요)
```

## API Documentation

**Flask + Swagger** 를 이용하여 내가 만든 API 를 문서화 시킬 수 있습니다.

![](https://i.imgur.com/i49F4mw.png)

자세한 구현 방법은 코드 참조 및 [Flasgger](https://github.com/flasgger/flasgger)

swagger 보기:
url/apidocs/#/경로로 이동

## 도커 사용법
```
먼저 git clone 을 통해 https://github.com/Ewha-Project-T/ewha_deploy을 복사해줍니다.
```
```
앱빌드 명령어
docker-compose build
docker-compose -f docker-compose.dev.yml build  // 이미지 빌드 
docker image ls
```

```
도커 사용시 명령어
docker-compose down : 도커 컨테이너를 중지 시키고 삭제 합니다.
docker-compose stop : 도커 컨테이너를 중지 시킵니다. 
docker-compose start : 도커 컨테이너를 실행합니다. 
docker-compose ps : 컨테이너 상태를 확인합니다.
docker-compose exec [servicename] [shell cmd] : 도커 컨테이너 접속 
접속시 컨테이너 명이 아니고 .yml 파일에 작성한  서비스 명(ubuntu)입니다.(ps명령어로 확인가능)
```

```
도커관리법
deploy는 그대로 두시면됩니다. deploy아래의 app폴더에 들어가 개발진행을 하면 됩니다.
변경사항은 git 명령어를 통해 저장하시면 됩니다.
```


