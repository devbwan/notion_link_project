# notion-link

공유된 Notion 문서 한 개를 읽어 제목과 중첩 본문 블록을 로컬 파일로 추출하는 Python CLI다. Notion 데이터베이스나 상태 속성은 사용하지 않는다.

## 설치

```powershell
python -m pip install -e ".[dev]"
```

`.env`에 읽기 권한이 있는 integration 토큰과 대상 문서 ID를 설정한다.

```dotenv
NOTION_TOKEN=secret_replace_me
NOTION_PAGE_ID=01234567-89ab-cdef-0123-456789abcdef
```

## 명령

```powershell
python -m notion_link validate-config
python -m notion_link sync --dry-run
python -m notion_link sync
pytest
ruff check .
```

기본 출력은 `output/notion/<page-id>.md`에 저장된다. 자세한 연결 및 설정 방법은 [빠른 시작](docs/getting-started.md)을 참고한다.
