# API/WebSocket

이 문서는 WebSocket API에 대한 설명입니다.

## Message
WebSocket은 `Message`를 통해 통신합니다.
`Message`는 다음과 같은 양식으로 작성되어 있습니다.

```json
{
    "header": {
		"event": <event-name>
	},
	"payload": <payload>
}
```

## Event
`Event`는 `Client-Event`와 `Server-Event`로 구분됩니다.

### Client-Event
`Client-Event`는 클라이언트에서 서버로 전송되는 이벤트입니다.
클라이언트가 Domain에서 정의된 특정 행동을 취하였을 경우 발행합니다.

### Server-Event
`Server-Event`는 서버에서 클라이언트로 전송되는 이벤트입니다.
Domain에서 정의된 특정 상태 변화가 발생하였을 경우 발행합니다.

각각의 `Event`는 다음 디렉토리에 문서화되어 있습니다.
- `Client-Event` -> `API/WebSocket/client`
- `Server-Event` -> `API/WebSocket/server`

`Event` 문서는 다음과 같은 양식으로 작성되어 있습니다.
```md
# EventName

Description of the event.

## payload
Description of the payload format.
```

## Event Naming Convention
`Event`의 이름은 다음과 같은 규칙을 따릅니다.
- 모든 글자는 대문자로 작성합니다.
- 단어는 하이픈(`-`)으로 구분합니다.
