# CURSOR-STATE

사용자의 `window`의 들어온 `Cursor`의 상태를 전송할 때 사용합니다.
다음과 같은 상황에 발생합니다.
- 사용자의 `window`에 `Cursor`가 들어왔을 때
- 사용자의 `window`에서 `Cursor`가 나갔을 때
- 사용자의 `window`에서 `Cursor`가 움직였을 때
- 사용자의 `window`에서 `Cursor`가 죽을 때
- 사용자의 `window`에서 `Cursor`가 부활했을 때
- 사용자의 `window`가 처음 표시될 때

## Payload
```json
{
    [
        <cursor_state>
    ]
}
```

cursor_state
```json
{
    "id": str,
    "position": Empty|Point = Empty,
    "pointer": Empty|Point|None = Empty, // Cursot가 pointing 하지 않으면 Pointer는 None일 수 있습니다
    "color": Empty|Color = Empty,
    "revive_at": Empty|datetime|None = Empty, // Cursot가 살아있으면 revive_at는 None일 수 있습니다
    "score": Empty|int = Empty
}
```
Empty: 해당 필드가 전송되지 않음을 의미합니다.
변경되지 않은 `Cursor`의 상태는 Empty입니다.