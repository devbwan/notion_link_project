# 변환 규칙과 설정 스키마

`config/mappings.yaml`은 Notion의 표시 이름을 내부 필드로 연결하고 검증, 정규화, 출력 규칙을 선언한다. 애플리케이션은 시작할 때 이 파일 전체를 검증하며 필수 키 누락과 알 수 없는 키를 오류로 처리한다. 저장소의 실행 기본값은 [`config/mappings.yaml`](../config/mappings.yaml), 복사용 템플릿은 [`config/mappings.yaml.example`](../config/mappings.yaml.example)이다.

## 전체 `mappings.yaml` 예시

```yaml
version: 1

notion:
  properties:
    title: "제목"
    status: "상태"
    category: "분류"
    content: "본문"
    tags: "태그"
    format: "출력 형식"
    created_at: "생성일"
    updated_at: "수정일"
    error_message: "오류 메시지"
  statuses:
    draft: "작성 중"
    request: "변환 요청"
    success: "완료"
    error: "오류"
  write_status: true

fields:
  type:
    source: category
    required: true
    normalize: [trim, lowercase]
  title:
    source: title
    required: true
    normalize: [trim, collapse_whitespace]
  content:
    source: content
    required: true
    normalize: [trim]
  tags:
    source: tags
    required: false
    normalize: [deduplicate]

output:
  default_format: markdown
  allowed_formats: [markdown, json, csv]
  root: output
  path_template: "{category}/{page_id}.{extension}"
  empty_values: omit
  csv:
    columns: [type, title, content, tags, notion_page_id]
    multi_value_separator: "|"
    encoding: utf-8
    include_header: true

datetime:
  input_timezone: Asia/Seoul
  output_timezone: UTC
  format: iso8601
```

## 최상위 구조

| 키 | 타입 | 필수 | 설명 |
|---|---|---:|---|
| `version` | 정수 | 예 | 설정 스키마 버전. MVP는 `1`만 허용 |
| `notion` | 객체 | 예 | 속성 이름과 상태 표시값 매핑 |
| `fields` | 객체 | 예 | 출력 필드별 입력, 필수 여부, 정규화 규칙 |
| `output` | 객체 | 예 | 형식, 경로, 빈 값, CSV 규칙 |
| `datetime` | 객체 | 예 | 입력 및 출력 시간대 정책 |

## `notion`

- `properties`: 논리 필드명을 실제 Notion 속성명에 매핑한다. 필수 키는 `title`, `status`, `category`, `content`, `tags`, `format`, `created_at`, `updated_at`, `error_message`이다.
- `statuses`: `draft`, `request`, `success`, `error`를 실제 Status 표시값에 매핑한다.
- `write_status`: boolean. `true`이면 처리 결과를 Notion에 기록한다.

## `fields`

각 출력 필드는 다음 키를 가진다.

| 키 | 타입 | 필수 | 설명 |
|---|---|---:|---|
| `source` | 문자열 | 예 | `notion.properties`의 논리 필드명 |
| `required` | boolean | 예 | 변환 전 필수값 검사 여부 |
| `normalize` | 문자열 목록 | 예 | 순서대로 적용할 정규화 함수 |

허용 정규화 함수는 `trim`, `collapse_whitespace`, `lowercase`, `slug`, `deduplicate`이다. 문자열에는 `trim`, `collapse_whitespace`, `lowercase`, `slug`만 적용할 수 있고 목록에는 `deduplicate`만 적용할 수 있다.

`source` 없이 생성되는 메타데이터인 `notion_page_id`는 설정 대상이 아니며 항상 출력에 포함한다.

## `output`

- `default_format`: `markdown`, `json`, `csv` 중 하나
- `allowed_formats`: 위 형식의 중복 없는 목록
- `root`: 저장소 기준 상대 경로. 절대 경로와 `..`는 허용하지 않음
- `path_template`: MVP에서는 `{category}/{page_id}.{extension}`만 허용
- `empty_values`: `omit` 또는 `null`. Markdown front matter와 JSON에 적용
- `csv.columns`: CSV 열 이름과 순서를 나타내는 목록
- `csv.multi_value_separator`: 목록 값을 한 셀에 결합할 한 글자 구분자
- `csv.encoding`: MVP에서는 `utf-8`만 허용
- `csv.include_header`: MVP에서는 `true`

경로의 `category` slug는 다음 순서로 만든다.

1. Unicode NFKC로 정규화하고 앞뒤 공백을 제거한다.
2. 대소문자가 있는 문자는 소문자로 바꾼다. 한글을 로마자로 음역하지 않으며 Unicode 문자와 숫자는 그대로 유지한다.
3. 공백, `_`와 연속된 하이픈을 단일 `-`로 바꾼다.
4. Unicode 문자·숫자·하이픈 이외의 문자, 경로 구분자와 제어 문자를 제거한다.
5. 앞뒤의 하이픈과 점을 제거한다. 결과가 비거나 `.`, `..`, Windows 예약명(`CON`, `PRN`, `AUX`, `NUL`, `COM1`~`COM9`, `LPT1`~`LPT9`)이면 `uncategorized`를 사용한다.
6. 최대 80 Unicode 코드 포인트로 자른 뒤 다시 끝 하이픈을 제거한다.

예를 들어 ` 개발 자료 / 2026 `은 `개발-자료-2026`이 된다. `page_id`는 하이픈을 포함한 전체 UUID를 사용한다.

설정 스키마 v1은 경로 안정성을 위해 현재 template 하나만 허용한다. 향후 스키마 v2에서는 `{slug}`, `{yyyy}`, `{mm}`, `{dd}`를 후보로 검토하되 `{page_id}`는 충돌 방지를 위해 필수로 유지한다. 새 placeholder는 경로 이동·고아 파일 처리와 마이그레이션 명령이 함께 설계되기 전에는 지원하지 않는다.

## `datetime`

- `input_timezone`: 시간대 없는 사용자 입력을 해석할 IANA 이름
- `output_timezone`: 직렬화 기준. MVP는 `UTC`
- `format`: MVP는 ISO 8601을 뜻하는 `iso8601`

Notion의 `created_time`과 `last_edited_time`처럼 오프셋이 있는 값은 원래 오프셋을 존중한 뒤 UTC로 변환한다. 시간대 없는 값은 `input_timezone`으로 해석한다.

## 형식별 빈 값 처리

- `empty_values: omit`: JSON 객체와 Markdown front matter에서 선택 필드를 생략한다. CSV는 열 구조를 유지해야 하므로 빈 셀을 쓴다.
- `empty_values: null`: JSON은 `null`, Markdown front matter는 YAML `null`, CSV는 빈 셀을 쓴다.
- 필수 필드의 빈 문자열, 빈 목록 또는 `null`은 정책과 관계없이 검증 오류다.

## CSV 직렬화

CSV는 RFC 4180 방식으로 쉼표, 큰따옴표, 줄바꿈이 포함된 필드를 인용하고 내부 큰따옴표를 두 번 쓴다. UTF-8 BOM은 추가하지 않는다. 다중 값은 설정의 구분자로 결합하며 각 값에 구분자가 포함되면 해당 페이지를 검증 오류로 처리한다.

예시:

```csv
type,title,content,tags,notion_page_id
meeting,"쉼표가 있는, 제목","첫 줄
둘째 줄",개발|일정,01234567-89ab-cdef-0123-456789abcdef
```

## 입력과 형식별 기대 출력

세 형식의 회귀 테스트는 다음 입력을 공통 fixture로 사용한다.

```text
제목: 회의 기록
분류: meeting
본문: 신규 기능 일정 논의
태그: 개발, 일정
페이지 ID: 01234567-89ab-cdef-0123-456789abcdef
```

JSON:

```json
{
  "type": "meeting",
  "title": "회의 기록",
  "content": "신규 기능 일정 논의",
  "tags": ["개발", "일정"],
  "notion_page_id": "01234567-89ab-cdef-0123-456789abcdef"
}
```

Markdown:

```markdown
---
type: meeting
tags:
  - 개발
  - 일정
notion_page_id: 01234567-89ab-cdef-0123-456789abcdef
---

# 회의 기록

신규 기능 일정 논의
```

CSV:

```csv
type,title,content,tags,notion_page_id
meeting,회의 기록,신규 기능 일정 논의,개발|일정,01234567-89ab-cdef-0123-456789abcdef
```

## 파일 갱신 규칙

한 페이지와 형식의 최종 경로는 항상 동일하다. 기존 파일과 새 콘텐츠의 체크섬이 같으면 쓰지 않고, 다르면 같은 디렉터리에 임시 파일을 쓴 뒤 원자적으로 교체한다. 설정에서 허용 형식을 제거해도 기존 산출물은 자동 삭제하지 않는다.
