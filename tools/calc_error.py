import json
import math
import sys


def vector_norm(values):
    return math.sqrt(sum(float(v) ** 2 for v in values))


def calculate_error(response):
    if response.get("code") != 0:
        raise ValueError(
            f"接口失败：code={response.get('code')}, "
            f"msg={response.get('msg')}"
        )

    data = response["data"]
    command = data["robotCommand"]

    # 三维平移残差
    translation_m = command["deltaTranslationM"]
    translation_error_m = vector_norm(translation_m)
    translation_error_mm = translation_error_m * 1000.0

    # 使用 deltaTransform 的旋转矩阵精确计算整体旋转误差
    transform = command["deltaTransform"]

    trace_r = (
        float(transform[0][0])
        + float(transform[1][1])
        + float(transform[2][2])
    )

    cos_angle = (trace_r - 1.0) / 2.0
    cos_angle = max(-1.0, min(1.0, cos_angle))

    rotation_error_rad = math.acos(cos_angle)
    rotation_error_deg = math.degrees(rotation_error_rad)

    # 局部坐标系平移分量
    local_translation_mm = [
        float(value) * 1000.0
        for value in translation_m
    ]

    # 基坐标系平移分量
    base_translation_m = data.get("baseTranslationDeltaM")

    if base_translation_m is not None:
        base_translation_mm = [
            float(value) * 1000.0
            for value in base_translation_m
        ]
    else:
        base_translation_mm = None

    result = {
        "translationErrorM": translation_error_m,
        "translationErrorMm": translation_error_mm,
        "rotationErrorRad": rotation_error_rad,
        "rotationErrorDeg": rotation_error_deg,
        "localTranslationMm": local_translation_mm,
        "baseTranslationMm": base_translation_mm,
    }

    return result


def main():
    if len(sys.argv) != 2:
        print("用法：python calc_error.py response.json")
        return 1

    json_path = sys.argv[1]

    with open(json_path, "r", encoding="utf-8") as file:
        response = json.load(file)

    result = calculate_error(response)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()
    print(
        f"三维平移残差："
        f"{result['translationErrorMm']:.6f} mm"
    )
    print(
        f"整体旋转残差："
        f"{result['rotationErrorDeg']:.6f}°"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())