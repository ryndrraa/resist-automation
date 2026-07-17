from __future__ import annotations


def to_float(value: object, *, field_name: str = "nilai") -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} harus berupa angka, ditemukan {value!r}.") from exc


def to_int(value: object, *, field_name: str = "nilai") -> int | None:
    number = to_float(value, field_name=field_name)
    if number is None:
        return None
    if not number.is_integer():
        raise ValueError(f"{field_name} harus berupa bilangan bulat, ditemukan {value!r}.")
    return int(number)


def metres_to_centimetres(value: float | None) -> float | int | None:
    if value is None:
        return None
    centimetres = value * 100
    nearest = round(centimetres)
    if abs(centimetres - nearest) < 1e-9:
        return int(nearest)
    return centimetres
