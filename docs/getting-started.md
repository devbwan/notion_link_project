# 빠른 시작

이 저장소는 현재 설계와 기본 설정 단계다. 아래의 CLI 및 설치 명령은 `pyproject.toml`과 `src/`가 구현된 뒤 사용할 목표 인터페이스이며, 현재 체크아웃에서는 아직 실행되지 않는다.

## 1. 사전 준비

- CPython 3.11 이상
- 대상 Notion database에 공유된 internal integration
- 읽기용 `Read content` 권한
- 상태와 오류를 Notion에 기록할 경우 `Update content` 권한

[Notion 입력 스키마](notion-schema.md)에 따라 속성을 만든다. 특히 상태 옵션의 기본값은 `작성 중`, `변환 요청`, `완료`, `오류`다.

## 2. 로컬 환경 구성

구현 완료 후 PowerShell에서 다음 순서로 준비한다.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
Copy-Item config\mappings.yaml.example config\mappings.local.yaml
```

`.env`에 실제 값을 입력한다.

```dotenv
NOTION_TOKEN=secret_replace_me
NOTION_DATABASE_ID=00000000-0000-0000-0000-000000000000
# database에 data source가 여러 개일 때만 필수
NOTION_DATA_SOURCE_ID=11111111-1111-1111-1111-111111111111
```

기본 설정을 그대로 쓸 때는 저장소의 `config/mappings.yaml`을 사용한다. 개인별 속성명이 다르면 Git에서 제외되는 `config/mappings.local.yaml`을 수정하고 `--config config/mappings.local.yaml`로 지정한다. 토큰과 실제 ID를 커밋하지 않는다.

## 3. 연결과 설정 확인

```powershell
python -m notion_link validate-config --config config\mappings.local.yaml
python -m notion_link sync --dry-run --config config\mappings.local.yaml
```

database에 data source가 하나면 프로그램이 자동 선택한다. 여러 개면 `NOTION_DATA_SOURCE_ID`를 지정해야 한다. `--dry-run`은 Notion 상태, 로컬 산출물과 SQLite 상태 DB를 변경하지 않는다.

## 4. 첫 동기화

Notion 페이지의 상태를 `변환 요청`으로 바꾼 뒤 실행한다.

```powershell
python -m notion_link sync --config config\mappings.local.yaml
```

기본 Markdown 결과는 다음 경로에 생성된다.

```text
output/<분류-slug>/<notion-page-id>.md
```

처리 상태는 `.state/notion-link.db`, 로그는 `logs/notion-link.log`에 저장된다. 두 경로와 `output/`은 Git에서 제외된다.

## 5. 테스트

```powershell
pytest
ruff check .
```

테스트는 실제 Notion 서비스에 연결하지 않고 저장된 fixture와 `pytest-httpx`를 사용해야 한다. 실제 API를 사용하는 통합 테스트는 별도의 명시적 옵션과 환경 변수로만 실행한다.

