# cursor-delete

Scope : cursor

커서 삭제시 점수 삭제 및 커서 삭제 알리기

## Trigger Event

> DataPayload[Cursor]

-   Cursor.DELETE

## Publish Event

-   Score.DELETE

    when: 점수가 삭제되었을 때

-   cursor-delete

    ***

    커서 삭제에 대한 External Message

## TestCase

-   NormalCase

    ***

    커서가 삭제되었기 때문에 그에 따라 점수도 삭제된다. <br>
    client에게 커서가 삭제된 것을 알린다.

    ### Check

    1. Score 삭제(Handler calling 확인)

        ***

        ScoreHandler의 Score.Delete publish test 의존

    2. cursor-delete publish
