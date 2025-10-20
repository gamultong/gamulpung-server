# MOVE

이는 사용자가 `Cursor`를 특정 위치로 이동을 요청할 때 사용됩니다.
다음과 같은 상황에 발생합니다.
- 사용자가 `opened-tile`을 좌클릭 할 때
- 사용자가 다음과 같은 `Event`를 실행하기에 거리가 멀 때
  - `OPEN-TILE`
  - `SET-FLAG`

## Payload
```json
{
    "position": {
        "x": int,
        "y": int
    }
}
```