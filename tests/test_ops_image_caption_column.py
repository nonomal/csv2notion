import logging
import re

import pytest

from csv2notion.cli import cli
from csv2notion.utils import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_image_caption_column_missing(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\na,b,c\n")

    test_db = db_maker.from_csv_head("a,b,c")

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--image-caption-column",
                "image caption",
                str(test_file),
            ]
        )

    assert "Image caption column 'image caption' not found in csv file" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_image_caption_column_empty(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b,image url,image caption\na,b,{test_image_url},\n")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--image-column",
            "image url",
            "--image-caption-column",
            "image caption",
            str(test_file),
        ]
    )

    table_header = test_db.header
    table_rows = test_db.rows

    image = table_rows[0].children[0]

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1
    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert len(table_rows[0].children) == 1

    assert image.caption == ""


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_image_caption_column_skip_for_new_db(tmp_path, db_maker, caplog):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b,image column\na,b,\n")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--image-caption-column",
                "image column",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    table_header = test_db.header
    table_rows = test_db.rows

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1
    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert len(table_rows[0].children) == 0


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_image_caption_column_ok(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b,image url,image caption\na,b,{test_image_url},test\n")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--image-column",
            "image url",
            "--image-caption-column",
            "image caption",
            str(test_file),
        ]
    )

    table_header = test_db.header
    table_rows = test_db.rows
    image = table_rows[0].children[0]

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1
    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert len(table_rows[0].children) == 1

    assert image.caption == "test"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_image_caption_column_overwrite(tmp_path, db_maker, caplog):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,image url,image caption\na,b,{test_image_url},test1\n")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--image-column",
                "image url",
                "--image-caption-column",
                "image caption",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)
    test_file.write_text(f"a,b,image url,image caption\na,b,{test_image_url},test2\n")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--image-column",
            "image url",
            "--image-caption-column",
            "image caption",
            "--merge",
            str(test_file),
        ]
    )

    table_header = test_db.header
    table_rows = test_db.rows
    image = table_rows[0].children[0]

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1
    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert len(table_rows[0].children) == 1

    assert image.caption == "test2"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_image_caption_column_keep(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b,image url,image caption\na,b,{test_image_url},test\n")

    test_db = db_maker.from_csv_head("a,b,image caption")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--image-column",
            "image url",
            "--image-caption-column",
            "image caption",
            "--image-caption-column-keep",
            str(test_file),
        ]
    )

    table_header = test_db.header
    table_rows = test_db.rows
    image = table_rows[0].children[0]

    assert table_header == {"a", "b", "image caption"}
    assert len(table_rows) == 1
    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert getattr(table_rows[0], "image caption") == "test"
    assert len(table_rows[0].children) == 1

    assert image.caption == "test"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_image_caption_column_keep_for_new_db(tmp_path, db_maker, caplog):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b,image file,image caption\na,b,,\n")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--image-column",
                "image file",
                "--image-caption-column",
                "image caption",
                "--image-caption-column-keep",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    table_header = test_db.header
    table_rows = test_db.rows

    assert table_header == {"a", "b", "image caption"}
    assert len(table_rows) == 1
    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert getattr(table_rows[0], "image caption") == ""
    assert len(table_rows[0].children) == 0
