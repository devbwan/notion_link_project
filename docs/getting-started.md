# 빠른 시작

이 프로그램은 Notion 데이터베이스를 조회하지 않는다. 지정한 Notion 문서 한 개의 제목과 본문 블록을 읽고, 중첩 블록과 페이지네이션을 따라가며 로컬 Markdown 파일로 저장한다.

## 1. 사전 준비

- CPython 3.11 이상
- `Read content` 권한이 있는 Notion internal integration
- integration에 공유된 대상 Notion 문서

Notion 문서의 **··· → 연결 → 연결 추가**에서 만든 integration을 선택한다. 문서가 공유되지 않으면 Notion API는 해당 페이지를 찾을 수 없다는 `404` 응답을 반환할 수 있다.

## 2. 설치와 환경 변수

PowerShell에서 다음 명령을 실행한다.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

루트의 `.env`에 다음 값을 입력한다.

```dotenv
NOTION_TOKEN=secret_replace_me
NOTION_PAGE_ID=01234567-89ab-cdef-0123-456789abcdef
```

`NOTION_PAGE_ID`는 문서 URL의 마지막 32자리 식별자다. 하이픈이 포함된 UUID 형식도 사용할 수 있다. 실제 토큰과 페이지 ID는 커밋하지 않는다.

## 3. 설정

기본 `config/mappings.yaml`은 다음을 제어한다.

```yaml
document:
  category: notion
  format: markdown
```

기본 결과 경로는 `output/notion/<page-id>.md`다. 개인 설정은 Git에서 제외되는 `config/mappings.local.yaml`에 복사한 뒤 `--config`로 지정할 수 있다.

## 4. 실행

설정 확인과 미리보기를 먼저 실행한다.

```powershell
python -m notion_link validate-config
python -m notion_link sync --dry-run
```

`--dry-run`은 문서를 읽고 추출 가능 여부를 확인하지만 `output/`과 `.state/`를 만들지 않는다. 실제 파일을 생성하려면 다음을 실행한다.

```powershell
python -m notion_link sync
```

처리 이력은 `.state/notion-link.db`에 저장된다. 문서의 `last_edited_time`이 이전 처리와 같으면 파일을 다시 쓰지 않는다.

## 5. 추출 범위

문단, 제목, 글머리표·번호 목록, 할 일, 인용, 콜아웃, 코드, 구분선, 수식과 링크 계열 블록을 Markdown으로 변환한다. 중첩 자식 블록도 재귀적으로 읽는다. 지원하지 않는 블록은 API가 제공하는 일반 텍스트가 있으면 텍스트만 보존한다.

## 6. 테스트

```powershell
pytest
ruff check .
```

테스트는 실제 Notion 서비스에 연결하지 않는다.
