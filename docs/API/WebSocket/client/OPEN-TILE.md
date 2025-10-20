# OPEN-TILE

이는 특정 `Tile`을 열기를 요청하는 이벤트입니다.
다음과 같은 상황에 발생합니다.
- 사용자가 `closed-tile`을 클릭했을 때

## Payload

```json
{
    "posiotion" : {
        "x": int,
        "y": int
    }
}
```