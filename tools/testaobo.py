import struct
from pymodbus.client import ModbusTcpClient


PLC_IP = "192.168.1.88"
PLC_PORT = 502

# 你的 P01
P01 = [
    -514.85,
    4.73,
    472.68,
    -3.141,
    0.0,
    0.757,
]


def float_to_words(value, word_order="low_high"):
    """
    float32 -> 两个 16bit word

    word_order:
        low_high  : 低字在前，高字在后
        high_low  : 高字在前，低字在后
    """

    # IEEE754 float32
    raw = struct.pack(">f", float(value))

    high_word, low_word = struct.unpack(">HH", raw)

    if word_order == "low_high":
        return [low_word, high_word]

    elif word_order == "high_low":
        return [high_word, low_word]

    else:
        raise ValueError("word_order 只能是 low_high 或 high_low")


def pose_to_registers(pose):
    """
    [X,Y,Z,RX,RY,RZ]
    -> 12 个 Word
    """

    registers = []

    for value in pose:
        words = float_to_words(
            value,
            word_order="low_high"
        )

        registers.extend(words)

    return registers


client = ModbusTcpClient(
    PLC_IP,
    port=PLC_PORT
)

if not client.connect():
    raise RuntimeError(
        f"连接 PLC 失败：{PLC_IP}:{PLC_PORT}"
    )

try:

    registers = pose_to_registers(P01)

    print("准备写入 D1020-D1031：")

    for i, value in enumerate(registers):
        print(
            f"D{1020 + i} = {value}"
        )

    # 一次写 12 个寄存器
    result = client.write_registers(
        address=1020,
        values=registers
    )

    if result.isError():
        raise RuntimeError(
            f"写入失败：{result}"
        )

    print()
    print("D1020-D1031 写入成功")

finally:
    client.close()