# Notion 입력 스키마

이 문서는 MVP가 기대하는 Notion data source의 속성과 연결 방법을 정의한다. 실제 속성 이름과 상태 표시값은 `config/mappings.yaml`에서 변경할 수 있으며, 아래 값은 기본값이다.

## API 버전 기준

`Notion-Version: 2026-03-11`은 미래 버전 표기가 아니다. 이 문서의 확인일인 **2026-07-14** 기준 Notion 공식 문서가 안내하는 최신 API 버전이다. API 버전명은 릴리스 날짜를 사용하므로 실행 환경의 현재 날짜와 비교해 추정하지 않고 [공식 versioning 문서](https://developers.notion.com/reference/versioning)로 확인한다.

프로젝트는 호환성을 위해 이 값을 코드 상수로 고정한다. 이후 최신 버전이 발표되어도 자동으로 변경하지 않으며, 마이그레이션 검토와 fixture 테스트를 통과한 뒤 명시적으로 올린다.

## 연결과 ID 탐색

1. Notion에서 internal integration을 만들고 대상 데이터베이스에 연결한다.
2. 데이터베이스 URL에서 `database_id`를 복사해 `NOTION_DATABASE_ID`에 설정한다.
3. 프로그램은 `Notion-Version: 2026-03-11`로 `GET /v1/databases/{database_id}`를 호출한다.
4. 응답의 `data_sources`가 하나면 그 ID를 자동 선택한다.
5. 둘 이상이면 자동 선택하지 않고 오류를 낸다. 사용할 ID를 Notion의 **Manage data sources → Copy data source ID**에서 복사해 `NOTION_DATA_SOURCE_ID`에 설정한다.
6. 선택한 ID로 data source 스키마를 조회한 뒤 아래 속성 타입을 검증한다.

Database에서 data source를 찾는 요청 예시:

```http
GET /v1/databases/00000000-0000-0000-0000-000000000000 HTTP/1.1
Host: api.notion.com
Authorization: Bearer secret_replace_me
Notion-Version: 2026-03-11
```

필요한 응답 구조만 축약하면 다음과 같다. `data_sources` 원소가 여러 개일 수 있다는 점을 전제로 처리한다.

```json
{
  "object": "database",
  "id": "00000000-0000-0000-0000-000000000000",
  "data_sources": [
    {
      "id": "11111111-1111-1111-1111-111111111111",
      "name": "콘텐츠 변환 요청"
    }
  ]
}
```

선택한 data source에서 처리 대상을 조회하는 요청 예시:

```http
POST /v1/data_sources/11111111-1111-1111-1111-111111111111/query HTTP/1.1
Host: api.notion.com
Authorization: Bearer secret_replace_me
Content-Type: application/json
Notion-Version: 2026-03-11

{
  "filter": {
    "property": "상태",
    "status": { "equals": "변환 요청" }
  },
  "page_size": 100
}
```

축약 응답은 `results`에 page 객체를 담으며 `has_more`가 `true`이면 `next_cursor`를 다음 요청의 `start_cursor`로 그대로 전달한다.

```json
{
  "object": "list",
  "results": [
    {
      "object": "page",
      "id": "22222222-2222-2222-2222-222222222222",
      "last_edited_time": "2026-07-14T07:00:00.000Z",
      "properties": {}
    }
  ],
  "has_more": false,
  "next_cursor": null
}
```

필수 환경 변수의 안전한 예시는 다음과 같다.

```dotenv
NOTION_TOKEN=secret_replace_me
NOTION_DATABASE_ID=00000000-0000-0000-0000-000000000000
# data source가 여러 개인 경우에만 필수
NOTION_DATA_SOURCE_ID=11111111-1111-1111-1111-111111111111
```

토큰과 실제 ID를 저장소에 커밋하지 않는다.

## 속성 정의

| 기본 속성명 | Notion 타입 | 필수 | 프로그램의 논리 필드 | 규칙 |
|---|---|---:|---|---|
| 제목 | `title` | 예 | `title` | 공백 제거 후 비어 있으면 오류 |
| 상태 | `status` | 예 | `status` | 아래 상태 매핑 중 하나여야 함 |
| 분류 | `select` | 예 | `category` | 출력 하위 디렉터리로 사용하기 전에 정규화 |
| 본문 | `rich_text` | 예 | `content` | rich text의 plain text를 순서대로 결합 |
| 태그 | `multi_select` | 아니요 | `tags` | 표시 순서를 유지하고 중복 제거 |
| 출력 형식 | `select` | 아니요 | `format` | 없으면 설정의 `markdown`; 허용값은 `markdown`, `json`, `csv` |
| 생성일 | `created_time` | 아니요 | `created_at` | UTC ISO 8601로 정규화 |
| 수정일 | `last_edited_time` | 예 | `updated_at` | 변경 감지 기준, UTC ISO 8601로 정규화 |
| 오류 메시지 | `rich_text` | 조건부 | `error_message` | `write_status: true`일 때 필수; 정제 후 최대 200 Unicode 코드 포인트 |

`출력 파일명` 속성은 페이지 ID 기반 경로로 정책을 확정했으므로 MVP 스키마에서 사용하지 않는다. 기존 데이터베이스에 남아 있어도 무시한다.

## 상태 매핑

코드는 한국어 문자열을 직접 비교하지 않고 설정의 논리 상태를 사용한다.

| 논리 상태 | 기본 Notion 표시값 | 의미 |
|---|---|---|
| `draft` | `작성 중` | 처리하지 않음 |
| `request` | `변환 요청` | 조회 및 처리 대상 |
| `success` | `완료` | 정상 처리됨 |
| `error` | `오류` | 검증·변환·저장 실패 |

처리 성공 후 상태 쓰기를 사용하려면 integration에 `Update content` 권한이 필요하다. 읽기 전용 모드에서는 로컬 상태만 갱신하고 Notion 상태는 변경하지 않는다.

오류 메시지에는 토큰, URL 쿼리, 본문 원문, 전체 페이지·database·data source ID를 포함하지 않는다. 줄바꿈과 제어 문자를 공백으로 바꾸고 연속 공백을 합친 뒤 200 Unicode 코드 포인트를 넘으면 197자와 `...`으로 잘라 기록한다. 상세 예외와 stack trace는 마스킹된 로컬 DEBUG 로그에만 남긴다.

## 스키마 검증 실패

다음 조건에서는 페이지 처리를 시작하지 않고 구성 오류로 종료한다.

- 설정에 지정한 필수 속성이 data source에 없음
- 실제 Notion 속성 타입이 표의 타입과 다름
- 상태 매핑 값이 중복되거나 비어 있음
- data source가 여러 개인데 `NOTION_DATA_SOURCE_ID`가 없음
- 지정한 data source가 해당 database의 자식이 아니거나 integration에 공유되지 않음
