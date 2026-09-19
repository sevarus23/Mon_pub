"""Checks for official source-list import scope and Excel ISSN normalization."""

import pytest

from scripts.import_scopus_sources import collect_issns, normalize_issn, valid_checksum


@pytest.mark.parametrize("value", [None, "", " ", 0, "00000000", "0000-0000", True, False,
                                   123.4, float("nan"), float("inf"), -1234,
                                   "9781604238464", "1234567", "0123--4567", "text"])
def test_rejects_blank_malformed_and_isbn_values(value):
    assert normalize_issn(value) is None


@pytest.mark.parametrize("value,expected", [
    ("00280836", "0028-0836"),
    (280836, "0028-0836"),
    (280836.0, "0028-0836"),
    (" 2434-561x ", "2434-561X"),
])
def test_normalizes_issn_without_losing_leading_zeroes(value, expected):
    assert normalize_issn(value) == expected


def test_checksum_audit_does_not_silently_remove_source_values():
    assert valid_checksum("0028-0836")
    assert valid_checksum("2434-561X")
    assert not valid_checksum("1234-5678")
    assert normalize_issn("1234-5678") == "1234-5678"


class Sheet:
    def __init__(self, rows):
        self.rows = rows

    def iter_rows(self, *, values_only):
        assert values_only
        return iter(self.rows)


class Workbook(dict):
    @property
    def sheetnames(self):
        return list(self)


def test_imports_main_and_serial_sources_including_historical_coverage():
    header = ("Sourcerecord ID", "Source Title", "ISSN", "EISSN", "Active or Inactive")
    workbook = Workbook({
        "Scopus Sources Aug. 2026": Sheet([
            header,
            (1, "Current", "00280836", "", "Active"),
            (2, "Historical", "00368075", None, "Inactive"),
            (3, "No ISSN", None, "", "Active"),
        ]),
        "Serial Conf. Proc. with Profile": Sheet([
            header, (4, "Serial conference", "2434561X", "00280836", "Inactive"),
        ]),
        # These sheets must not even be read, including their valid ISSNs.
        "Accepted Titles Aug. 2026": None,
        "All Conf. Proceedings Jun. 2026": None,
        "Discontinued Titles Aug. 2026": None,
    })
    issns, report = collect_issns(workbook)
    assert issns == {"0028-0836", "0036-8075", "2434-561X"}
    assert report["unique_issns"] == 3
    assert report["sheets"][0]["data_rows"] == 3
    assert report["sheets"][0]["rejected_nonempty_cells"] == 0


def test_changed_workbook_schema_fails_instead_of_replacing_snapshot():
    with pytest.raises(ValueError, match="Expected one"):
        collect_issns(Workbook({"Renamed Sources": None}))
    with pytest.raises(ValueError, match="Missing required columns"):
        collect_issns(Workbook({
            "Scopus Sources Aug. 2026": Sheet([("ISBN",)]),
            "Serial Conf. Proc. with Profile": None,
        }))
