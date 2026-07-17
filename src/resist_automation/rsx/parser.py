from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

from ..exceptions import InvalidRSXError, MissingRSXElementError
from ..models import BuildingData, EarthquakeData, ParsedRSX, RSXMetadata, StructureAxis
from ..utils.number_utils import metres_to_centimetres, to_float, to_int


LOGGER = logging.getLogger("resist_automation.rsx.parser")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _iter_named(root: ET.Element, *names: str) -> Iterable[ET.Element]:
    wanted = {name.casefold() for name in names}
    return (element for element in root.iter() if _local_name(element.tag).casefold() in wanted)


def _find_first(root: ET.Element, *names: str) -> ET.Element | None:
    return next(iter(_iter_named(root, *names)), None)


def _attr(element: ET.Element | None, *names: str) -> str | None:
    if element is None:
        return None
    normalized = {key.casefold(): value for key, value in element.attrib.items()}
    for name in names:
        if name.casefold() in normalized:
            return normalized[name.casefold()]
    return None


def _float_attr(element: ET.Element | None, *names: str) -> float | None:
    value = _attr(element, *names)
    return to_float(value, field_name="/".join(names))


def _int_attr(element: ET.Element | None, *names: str) -> int | None:
    value = _attr(element, *names)
    return to_int(value, field_name="/".join(names))


def _point_data(elements: Iterable[ET.Element]) -> list[dict[str, str]]:
    return [dict(element.attrib) for element in elements]


def _parse_building(root: ET.Element) -> BuildingData:
    building = _find_first(root, "Building")
    if building is None:
        raise MissingRSXElementError(
            "File dapat dibuka sebagai XML, tetapi elemen <Building> tidak ditemukan."
        )

    storeys = _find_first(building, "Storeys")
    storey = _find_first(storeys, "Storey") if storeys is not None else None
    roof = _find_first(building, "Roof")
    perimeter = _find_first(building, "Perimeter")
    area_element = _find_first(building, "Area", "FloorArea")
    wind = _find_first(building, "Wind")

    perimeter_length = _float_attr(perimeter, "length", "perimeter_length")
    if perimeter_length is None:
        perimeter_length = _float_attr(building, "perimeter", "perimeter_length")

    area = _float_attr(area_element, "value", "area")
    if area is None and area_element is not None and area_element.text:
        area = to_float(area_element.text.strip(), field_name="area")
    if area is None:
        area = _float_attr(perimeter, "area") or _float_attr(building, "area")

    perimeter_points: list[dict[str, str]] = []
    if perimeter is not None:
        perimeter_points = _point_data(_iter_named(perimeter, "Point", "PerimeterPoint"))

    return BuildingData(
        attributes=dict(building.attrib),
        num_storeys=_int_attr(storeys, "num_storeys", "number", "count"),
        storey_height=_float_attr(storey, "height"),
        roof_height=_float_attr(roof, "height"),
        area=area,
        perimeter_length=perimeter_length,
        perimeter_points=perimeter_points,
        wind_region=_attr(wind, "region", "wind_region"),
    )


def _parse_structure(container: ET.Element, direction: str) -> StructureAxis:
    frame = _find_first(container, "BracedFrame")
    braces = _find_first(frame, "Braces") if frame is not None else None
    centre = _find_first(container, "CentreOfRigidity", "CenterOfRigidity")
    layout = _find_first(container, "Layout")
    depth_m = _float_attr(braces, "depth")
    points = _point_data(_iter_named(layout, "Point", "LayoutPoint")) if layout is not None else []
    return StructureAxis(
        direction=direction,  # type: ignore[arg-type]
        class_name=_attr(frame, "class"),
        bracing_type=_attr(frame, "bracing_type", "bracingType"),
        depth_m=depth_m,
        depth_cm=metres_to_centimetres(depth_m),
        bay_length=_float_attr(frame, "bay_length"),
        num_bays=_int_attr(frame, "num_bays"),
        num_braced_bays=_int_attr(frame, "num_br_bays", "num_braced_bays"),
        num_components=_int_attr(container, "num_components"),
        centre_of_rigidity=dict(centre.attrib) if centre is not None else {},
        layout_points=points,
    )


def _parse_structures(root: ET.Element) -> dict[str, StructureAxis]:
    found: dict[str, StructureAxis] = {}
    for element in _iter_named(root, "LateralResistStructure"):
        direction = (_attr(element, "direction") or "").strip().lower()
        if direction in {"x", "y"} and direction not in found:
            found[direction] = _parse_structure(element, direction)
    missing = [axis.upper() for axis in ("x", "y") if axis not in found]
    if missing:
        raise MissingRSXElementError(
            "Struktur lateral arah " + " dan ".join(missing) + " tidak ditemukan dalam file RSX."
        )
    return found


def parse_rsx(path: Path) -> ParsedRSX:
    path = Path(path).expanduser().resolve()
    if not path.exists():
        raise InvalidRSXError(f"File RSX tidak ditemukan: {path}")
    if not path.is_file():
        raise InvalidRSXError(f"Path RSX bukan file: {path}")
    if path.suffix.lower() != ".rsx":
        raise InvalidRSXError(f"File harus berekstensi .rsx: {path.name}")

    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise InvalidRSXError(f"XML pada {path.name} rusak: {exc}") from exc
    except OSError as exc:
        raise InvalidRSXError(f"File {path.name} tidak dapat dibaca: {exc}") from exc

    root = tree.getroot()
    if _local_name(root.tag).casefold() != "resist":
        raise InvalidRSXError(
            f"Root XML harus <RESIST>, ditemukan <{_local_name(root.tag)}> pada {path.name}."
        )

    earthquake = _find_first(root, "Earthquake")
    if earthquake is None:
        raise MissingRSXElementError(
            "File dapat dibuka sebagai XML, tetapi elemen <Earthquake> tidak ditemukan."
        )
    pga = _float_attr(earthquake, "zone_factor")
    if pga is None:
        raise MissingRSXElementError(
            "Elemen <Earthquake> ditemukan, tetapi atribut zone_factor tidak tersedia."
        )

    metadata = RSXMetadata(
        version=_attr(root, "version"),
        country_code=_attr(root, "country_code"),
        code_year=_attr(root, "code_year"),
        language=_attr(root, "language"),
        modeller=_attr(root, "modeller"),
        file_date=_attr(root, "file_date"),
        project=_attr(root, "project"),
        raw=dict(root.attrib),
    )
    warnings: list[str] = []
    if metadata.version and not metadata.version.startswith("4.0"):
        warnings.append(
            f"Versi RESIST {metadata.version} belum tervalidasi; parser tetap mencoba membaca struktur XML."
        )

    parsed = ParsedRSX(
        source_path=path,
        metadata=metadata,
        building=_parse_building(root),
        earthquake=EarthquakeData(pga=pga, attributes=dict(earthquake.attrib)),
        structures=_parse_structures(root),
        warnings=warnings,
    )
    LOGGER.info("action=parse_rsx source=%s pga=%s", path, pga)
    return parsed
