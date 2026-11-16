from services.plate_validator import REGION_MAP, validate_plate


def test_standard_plate_formats_and_maps_region():
    result = validate_plate("b1234xyz")

    assert result["valid"] is True
    assert result["status"] == "valid"
    assert result["plate"] == "B 1234 XYZ"
    assert result["region_code"] == "B"
    assert result["region"] == "DKI Jakarta"


def test_special_plate_is_valid():
    result = validate_plate("RI 1")

    assert result["valid"] is True
    assert result["status"] == "valid"
    assert result["region"] == "Kendaraan Dinas Khusus"


def test_invalid_ocr_is_marked_invalid():
    result = validate_plate("###")

    assert result["valid"] is False
    assert result["status"] == "invalid"


def test_dg_region_mapping_is_maluku_utara():
    assert REGION_MAP["DG"] == "Maluku Utara"
