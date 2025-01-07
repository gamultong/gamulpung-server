from dataclasses import dataclass


@dataclass
class Tiles:
    data: bytearray

    def to_str(self):
        return self.data.hex()

    def hide_info(self):
        """
        타일들의 mine, number 정보를 제거한다.
        타일의 상태가 CLOSED일 때만 해당한다.

        주의: Tiles 데이터가 변형된다.
        """
        opened = 0b10000000
        mask = 0b10111000
        for idx in range(len(self.data)):
            b = self.data[idx]
            if b & opened:
                continue

            b &= mask
            self.data[idx] = b
