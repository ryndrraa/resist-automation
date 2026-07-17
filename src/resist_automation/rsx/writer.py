from __future__ import annotations

import os
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from ..exceptions import InvalidRSXError, OutputExistsError
from ..models import ParsedRSX
from .parser import parse_rsx


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find_first(root: ET.Element, name: str) -> ET.Element | None:
    wanted = name.casefold()
    return next(
        (element for element in root.iter() if _local_name(element.tag).casefold() == wanted),
        None,
    )


def _structures(root: ET.Element) -> dict[str, ET.Element]:
    result: dict[str, ET.Element] = {}
    for element in root.iter():
        if _local_name(element.tag).casefold() != "lateralresiststructure":
            continue
        direction = element.attrib.get("direction", "").strip().lower()
        if direction in {"x", "y"} and direction not in result:
            result[direction] = element
    return result


def _unique_output_path(output_directory: Path, filename: str) -> Path:
    requested = output_directory / filename
    if not requested.exists():
        return requested
    stem, suffix = requested.stem, requested.suffix
    counter = 2
    while True:
        candidate = output_directory / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def generate_rsx_variant(
    source_path: Path,
    output_path: Path,
    *,
    pga: float,
    depth_x_m: float,
    depth_y_m: float,
    modeller: str | None = None,
    project: str | None = None,
    allow_overwrite: bool = False,
) -> ParsedRSX:
    source_path = Path(source_path).expanduser().resolve()
    output_path = Path(output_path).expanduser().resolve()
    if output_path == source_path:
        raise InvalidRSXError("Generator tidak boleh menimpa file RSX sumber.")
    if output_path.exists() and not allow_overwrite:
        raise OutputExistsError(f"File output sudah ada: {output_path.name}")
    if output_path.suffix.lower() != ".rsx":
        raise InvalidRSXError("File hasil generator harus berekstensi .rsx.")
    if pga < 0 or depth_x_m < 0 or depth_y_m < 0:
        raise InvalidRSXError("PGA dan dimensi brace tidak boleh negatif.")

    # Validasi sumber lebih dahulu tanpa pernah mengubahnya.
    parse_rsx(source_path)
    try:
        tree = ET.parse(source_path)
    except (ET.ParseError, OSError) as exc:
        raise InvalidRSXError(f"RSX sumber tidak dapat diproses: {exc}") from exc
    root = tree.getroot()
    earthquake = _find_first(root, "Earthquake")
    if earthquake is None:
        raise InvalidRSXError("Elemen <Earthquake> tidak ditemukan pada RSX sumber.")
    earthquake.set("zone_factor", f"{pga:g}")

    structures = _structures(root)
    for axis, depth in (("x", depth_x_m), ("y", depth_y_m)):
        container = structures.get(axis)
        braces = _find_first(container, "Braces") if container is not None else None
        if braces is None:
            raise InvalidRSXError(f"Elemen <Braces> sumbu {axis.upper()} tidak ditemukan.")
        braces.set("depth", f"{depth:g}")

    if modeller is not None and modeller.strip():
        root.set("modeller", modeller.strip())
    if project is not None and project.strip():
        root.set("project", project.strip())
    root.set("file_date", datetime.now().strftime("%d %B %Y %H:%M:%S"))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=".resist-rsx-",
        suffix=".rsx",
        dir=output_path.parent,
        delete=False,
    )
    temp_path = Path(handle.name)
    handle.close()
    try:
        tree.write(temp_path, encoding="utf-8", xml_declaration=True)
        parse_rsx(temp_path)
        os.replace(temp_path, output_path)
        return parse_rsx(output_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def generate_rsx_batch(
    source_path: Path,
    output_directory: Path,
    *,
    pga_values: list[float],
    depth_x_values_m: list[float],
    depth_y_values_m: list[float],
    structure_x_id: str,
    structure_y_id: str,
    modeller: str | None = None,
    project: str | None = None,
) -> list[ParsedRSX]:
    if not pga_values or not depth_x_values_m or not depth_y_values_m:
        raise InvalidRSXError("Pilih minimal satu PGA dan satu dimensi untuk tiap sumbu.")
    structure_x_id = structure_x_id.strip().upper()
    structure_y_id = structure_y_id.strip().upper()
    if not structure_x_id or not structure_y_id:
        raise InvalidRSXError("ID struktur X dan Y wajib diisi untuk penamaan file.")
    output_directory = Path(output_directory).expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    generated: list[ParsedRSX] = []
    multiple_dimensions = len(depth_x_values_m) * len(depth_y_values_m) > 1
    for pga in pga_values:
        for depth_x in depth_x_values_m:
            for depth_y in depth_y_values_m:
                base_name = f"{pga:g} {structure_x_id}-{structure_y_id}"
                if multiple_dimensions:
                    base_name += f" dx-{depth_x:g}_dy-{depth_y:g}"
                output_path = _unique_output_path(output_directory, base_name + ".rsx")
                generated.append(
                    generate_rsx_variant(
                        source_path,
                        output_path,
                        pga=pga,
                        depth_x_m=depth_x,
                        depth_y_m=depth_y,
                        modeller=modeller,
                        project=project,
                    )
                )
    return generated
