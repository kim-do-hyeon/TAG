# Project TAG
### 프로젝트 소개
### 팀원 소개
<div align="center">

|[ 박승현 ]<br/>PM<br/>|[ 김도현 ]<br/>Service Developer<br/> | [ 박시우 ]<br/>Data Analyze<br/>| [ 이주영 ]<br/>RAG Developer<br/>| [ 박지혜 ]<br/>AI Developer<br/>
| :----------------------------------------------------------: | :---------------------------------------------: | :------: | :-------------------------------------------------: | :------: |
|<img src = "https://github.com/user-attachments/assets/a714954b-46da-4902-b52f-8a1374a7b8c9" width="150"> | <img src = "https://github.com/user-attachments/assets/674c678a-57b1-49a0-8bc1-10860df25a67" width="150"> | <img src = "https://github.com/user-attachments/assets/d1927bce-2d7d-4426-8529-26f69566308b" width="150">  | <img src = "https://github.com/user-attachments/assets/8ad8cf49-13d7-4033-8134-2a9a53f63b64" width="150"> | <img src = "https://github.com/user-attachments/assets/cd75e1e6-9ad0-4b8d-b3fc-18f686eda4d2" width="150">

## 테스트 데이터
<a href="http://file.system32.kr:5000/sharing/COXRyml8W">Download Scenario Sample</a>

### 시나리오 내용

### 시나리오 1
전체 과정
> USB 연결 → 기밀 문서 복사 → (문서 이름 or 확장자 변경) → USB 연결 해제 → 외부로 USB 유출
- 2024년 9월 24일 오후 8시 8분
> USB 연결 (Samsung Flash)
- 2024년 9월 24일 오후 8시 9분
> TAG_기밀자료_1 ~ 8.hwp 복사
2024년 9월 24일 오후 8시 9분
>TAG_기밀자료_1 ~ 8.hwp → 문서_1 ~ 8.hwp 로 이름변경
2024년 9월 24일 오후 8시 10분
> USB 연결 해제

### 시나리오 2
- 전체 과정
> USB 연결 → 외부 클라우드 스토리지에 업로드 → 복사본 삭제 → USB 연결 해제
- 2024년 9월 24일 오후 8시 14분
> USB  연결 (SanDisk)
- 2024년 9월 24일 오후 8시 15분 
> http://192.168.55.136:8888 접속후 TAG_도면_1 ~ 5.clip 파일 업로드
- 2024년 9월 24일 오후 8시 16분
> TAG_도면_1 ~ 5.clip 파일 영구 삭제
- 2024년 9월 24일 오후 8시 17분
> USB 연결 해제

### 시나리오 3
- 전체 과정
> USB 연결 → 프린터를 사용한 내부 파일 출력 → 원본파일 삭제 → USB 연결 해제
- 2024년 9월 24일 오후 8시 26분
> USB 연결 (SG Flash)
- 2024년 9월 24일 오후 8시 27분
> TAG_기밀자료_9 ~ 15 출력
- 2024년 9월 24일 오후 8시 28분
> TAG_기밀자료_9 ~ 15 삭제 (일반삭제 / 휴지통에 있음)
- 2024년 9월 24일 오후 8시 30분 
> USB 연결 해제

## 📎 커밋 규칙

기본적으로 각 기술에 맞게 커밋을 추가한다.

|**타입 리스트**|**설명**|
|:---:|:---:|
|🐞 Fix|올바르지 않은 동작(버그)을 고친 경우|
|🌊 Feat|새로운 기능을 추가한 경우|
|✨ Add|feat 이외의 부수적인 코드, 라이브러리 등을 추가한 경우, 새로운 파일(Component나 Activity 등)을 생성한 경우도 포함|
|🩹 Refactor|내부 로직은 변경하지 않고 기존의 코드를 개선한 경우, 클래스명 수정&가독성을 위해 변수명을 변경한 경우도 포함|
|🗑️ Remove|코드, 파일을 삭제한 경우, 필요 없는 주석 삭제도 포함|
|🚚 Move|fix, refactor 등과 관계 없이 코드, 파일 등의 위치를 이동하는 작업만 수행한 경우|
|🎨 Style|내부 로직은 변경하지 않고 코드 스타일, 포맷 등을 수정한 경우, 줄 바꿈, 누락된 세미콜론 추가 등의 작업도 포함|
|💄 Design|CSS 등 사용자 UI 디자인을 추가, 수정한 경우|
|📝 Comment|필요한 주석을 추가, 수정한 경우(❗ 필요 없는 주석을 삭제한 경우는 remove)|
|📚 Docs|문서를 추가, 수정한 경우|
|🔧 Test|테스트 코드를 추가, 수정, 삭제한 경우|
|🎸 Chore|위 경우에 포함되지 않는 기타 변경 사항|
|🙈 gitignore|ignore파일 추가 및 수정|
