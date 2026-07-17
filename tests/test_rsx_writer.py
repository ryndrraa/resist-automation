from __future__ import annotations

from pathlib import Path

from resist_automation.rsx.writer import generate_rsx_batch, generate_rsx_variant
from resist_automation.utils.file_utils import sha256_file


def test_generator_changes_only_supported_numeric_parameters(sample_rsx: Path, tmp_path: Path) -> None:
    original_hash = sha256_file(sample_rsx)
    output = tmp_path / "0.4 BFCTST-BFCTST.rsx"

    parsed = generate_rsx_variant(
        sample_rsx,
        output,
        pga=0.4,
        depth_x_m=0.2,
        depth_y_m=0.3,
        modeller="Penguji",
        project="Varian Aman",
    )

    assert sha256_file(sample_rsx) == original_hash
    assert parsed.earthquake.pga == 0.4
    assert parsed.structures["x"].depth_cm == 20
    assert parsed.structures["y"].depth_cm == 30
    assert parsed.metadata.modeller == "Penguji"
    assert parsed.metadata.project == "Varian Aman"


def test_batch_generator_never_silently_overwrites(sample_rsx: Path, tmp_path: Path) -> None:
    first = generate_rsx_batch(
        sample_rsx,
        tmp_path,
        pga_values=[0.4, 0.5],
        depth_x_values_m=[0.1],
        depth_y_values_m=[0.1],
        structure_x_id="BFCTST",
        structure_y_id="BFCTST",
    )
    second = generate_rsx_batch(
        sample_rsx,
        tmp_path,
        pga_values=[0.4],
        depth_x_values_m=[0.1],
        depth_y_values_m=[0.1],
        structure_x_id="BFCTST",
        structure_y_id="BFCTST",
    )
    assert len(first) == 2
    assert len(second) == 1
    assert second[0].source_path.name == "0.4 BFCTST-BFCTST (2).rsx"
