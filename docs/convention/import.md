# import convention

프로젝트의 import convention은 다음과 같다.
- module단위로 들여쓴다.(ex1)
- 다음과 같은 우선순위로 module을 나열한다.
    1. `bultin-module`
    2. `core`
    3. `utils`
    4. `impl-module`
- import하는 feature가 많아지면 괄호를 사용해 나열한다.(ex2)

## 예시
#### ex1)
```py
from bultin-module import some_feature

from core-module import some_feature

from utils-module import some_feature

from impl-module import some_feature
```

#### ex2)
```py
from some-module import (
    some_feature_1,
    some_feature_2,
    some_feature_3
)
```