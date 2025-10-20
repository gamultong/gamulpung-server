# SET-WINDOW-SIZE

이는 `window`의 크기를 설정하는데에 사용됩니다.
다음과 같은 상황에 발생합니다.
- 클라이언트가 `window`의 크기를 변경했을 때
- 클라이언트가 처음 접속하여 `window`의 크기를 서버에 알릴 때

## Payload

```json
{
  "width": int,
  "height": int
}
```