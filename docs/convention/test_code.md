# Test Code

test code의 convention은 다음과 같다.
- `unittest`를 사용한다.
- `TestCase`의 이름은 `<테스트 대상>_TestCase`이다.(ex1)
- 모듈의 모든 `TestCase`를 `Module/test/__init__.py`에서 import하며 이를 실행할 수 있어야 한다.(ex2)

## 예시
#### ex1)
```py
from unittest import TestCase

class SomeFeature_TestCase(TestCase):
    def test_some_case(self):
        ...
```

#### ex2)
```py
from .feature_1 import Feature_1_TestCase
from .feature_2 import Feature_2_TestCase

if __name__ == "__main__":
    from unittest import main
    main()
```