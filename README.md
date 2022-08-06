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



