import io
import csv

import pytest

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

import zipfile
import re

from app.modules.file_masking.service import (
    preview_file,
    mask_file,
    FileMaskingValidationError,
    MAX_FILE_SIZE,
)


def make_xlsx():
    """生成包含两个工作表的测试 Excel。"""

    workbook = Workbook()

    sheet1 = workbook.active
    sheet1.title = "客户信息"

    sheet1.append(["客户姓名", "联系电话", "邮箱"])
    sheet1.append(["张三", "13812345678", "abc@qq.com"])
    sheet1.append(["李四", "13912345678", "def@qq.com"])

    sheet2 = workbook.create_sheet("身份信息")

    sheet2.append(["身份证号码", "家庭住址"])
    sheet2.append([
        "110101199001011234",
        "北京市朝阳区",
    ])

    output = io.BytesIO()
    workbook.save(output)

    return output.getvalue()


def test_preview_csv():
    content = (
        "姓名,手机号,邮箱\n"
        "张三,13812345678,abc@qq.com\n"
        "李四,13912345678,def@qq.com\n"
    ).encode("utf-8")

    result = preview_file("customers.csv", content)

    assert result["file_type"] == "csv"
    assert result["total_sensitive_columns"] >= 3

    columns = result["sheets"][0]["columns"]

    assert columns[1]["sensitive_type"] == "phone"
    assert columns[2]["sensitive_type"] == "email"


def test_preview_gb18030_csv():
    content = (
        "客户姓名,联系电话\n"
        "张三,13812345678\n"
        "李四,13912345678\n"
    ).encode("gb18030")

    result = preview_file("customers.csv", content)

    assert result["encoding"] == "gb18030"
    assert result["total_sensitive_columns"] >= 1


def test_preview_utf8_bom_csv():
    content = (
        "\ufeff姓名,手机号\n"
        "张三,13812345678\n"
    ).encode("utf-8")

    result = preview_file("customers.csv", content)

    assert result["encoding"] == "utf-8-sig"
    assert result["file_type"] == "csv"


def test_preview_xlsx_multiple_sheets():
    content = make_xlsx()

    result = preview_file("customers.xlsx", content)

    assert result["file_type"] == "xlsx"
    assert len(result["sheets"]) == 2

    first_sheet = result["sheets"][0]
    second_sheet = result["sheets"][1]

    assert first_sheet["sheet_name"] == "客户信息"
    assert second_sheet["sheet_name"] == "身份信息"

    assert (
        first_sheet["columns"][1]["sensitive_type"]
        == "phone"
    )

    assert (
        second_sheet["columns"][0]["sensitive_type"]
        == "id_card"
    )


def test_preview_does_not_expose_original_values():
    content = (
        "姓名,手机号\n"
        "张三,13812345678\n"
    ).encode("utf-8")

    result = preview_file("customers.csv", content)

    serialized = str(result)

    assert "13812345678" not in serialized
    assert "张三" not in serialized


def test_reject_invalid_extension():
    with pytest.raises(FileMaskingValidationError):
        preview_file(
            "customers.txt",
            b"hello",
        )


def test_reject_path_traversal_filename():
    with pytest.raises(FileMaskingValidationError):
        preview_file(
            "../customers.csv",
            b"name,phone\n",
        )


def test_reject_oversized_file():
    content = b"a" * (MAX_FILE_SIZE + 1)

    with pytest.raises(FileMaskingValidationError):
        preview_file("large.csv", content)


def test_reject_empty_file():
    with pytest.raises(FileMaskingValidationError):
        preview_file("empty.csv", b"")


def test_reject_invalid_xlsx():
    with pytest.raises(FileMaskingValidationError):
        preview_file(
            "broken.xlsx",
            b"PK invalid xlsx content",
        )


def test_reject_xlsx_disguised_as_csv():
    content = make_xlsx()

    with pytest.raises(FileMaskingValidationError):
        preview_file("fake.csv", content)



def test_formula_not_used_as_sample():
    import csv
    import io

    # 使用标准 CSV 写入器生成合法 CSV
    output = io.StringIO(newline="")
    writer = csv.writer(output)

    writer.writerow(["联系电话"])
    writer.writerow(['=CONCAT("138","12345678")'])

    content = output.getvalue().encode("utf-8")

    result = preview_file("formula.csv", content)

    column = result["sheets"][0]["columns"][0]

    # 公式不能作为手机号识别样本
    assert column["sensitive_type"] == "phone"
    assert column["sample_count"] == 0
    assert column["matched_count"] == 0




def test_preview_xlsx_with_incorrect_dimension():
    """
    模拟 Excel 内部尺寸错误：
    实际有三列，但 XML 声明只有 A1:A1。
    """

    original = make_xlsx()

    source = zipfile.ZipFile(
        io.BytesIO(original)
    )

    output = io.BytesIO()

    with zipfile.ZipFile(
        output,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as target:

        for item in source.infolist():

            data = source.read(item.filename)

            if item.filename == "xl/worksheets/sheet1.xml":

                xml = data.decode("utf-8")

                xml = re.sub(
                    r'<dimension ref="[^"]+"\s*/>',
                    '<dimension ref="A1:A1"/>',
                    xml,
                    count=1,
                )

                data = xml.encode("utf-8")

            target.writestr(item, data)

    source.close()

    result = preview_file(
        "customers.xlsx",
        output.getvalue(),
    )

    first_sheet = result["sheets"][0]

    assert len(first_sheet["columns"]) == 3

    assert first_sheet["sampled_rows"] == 2

    assert (
        first_sheet["columns"][1]["sensitive_type"]
        == "phone"
    )




def test_mask_csv_only_selected_column():
    content = (
        "姓名,手机号,余额,备注\n"
        "张三,13812345678,-12.5,普通文本\n"
        "李四,13912345678,20,=1+1\n"
    ).encode("utf-8")

    result = mask_file(
        "customers.csv",
        content,
        [{
            "sheet_name": "CSV",
            "column_index": 2,
            "sensitive_type": "phone",
        }],
    )

    rows = list(csv.reader(
        io.StringIO(result["content"].decode("utf-8"))
    ))

    assert rows[1][0] == "张三"
    assert rows[1][1] == "138****5678"
    assert rows[1][2] == "-12.5"
    assert rows[2][3] == "'=1+1"


def test_mask_csv_preserves_gb18030():
    content = (
        "姓名,手机号\n"
        "张三,13812345678\n"
    ).encode("gb18030")

    result = mask_file(
        "customers.csv",
        content,
        [{
            "sheet_name": "CSV",
            "column_index": 2,
            "sensitive_type": "phone",
        }],
    )

    decoded = result["content"].decode("gb18030")

    assert "138****5678" in decoded
    assert result["encoding"] == "gb18030"


def test_mask_xlsx_multiple_sheets_and_styles():
    original = make_xlsx()

    source = load_workbook(io.BytesIO(original))

    source["客户信息"]["B1"].font = Font(bold=True)

    source["客户信息"].column_dimensions["B"].width = 26

    styled = io.BytesIO()

    source.save(styled)
    source.close()

    result = mask_file(
        "customers.xlsx",
        styled.getvalue(),
        [{
            "sheet_name": "客户信息",
            "column_index": 2,
            "sensitive_type": "phone",
        }],
    )

    workbook = load_workbook(
        io.BytesIO(result["content"])
    )

    try:
        sheet = workbook["客户信息"]

        assert sheet["B2"].value == "138****5678"
        assert sheet["A2"].value == "张三"
        assert sheet["C2"].value == "abc@qq.com"

        assert sheet["B1"].font.bold is True
        assert sheet.column_dimensions["B"].width == 26

        assert (
            workbook["身份信息"]["A2"].value
            == "110101199001011234"
        )

    finally:
        workbook.close()


def test_mask_xlsx_skips_formula_cells():
    workbook = Workbook()

    sheet = workbook.active
    sheet.title = "测试"

    sheet.append(["联系电话"])
    sheet.append(["=1+1"])
    sheet.append(["13812345678"])

    source = io.BytesIO()

    workbook.save(source)
    workbook.close()

    result = mask_file(
        "formula.xlsx",
        source.getvalue(),
        [{
            "sheet_name": "测试",
            "column_index": 1,
            "sensitive_type": "phone",
        }],
    )

    output = load_workbook(
        io.BytesIO(result["content"]),
        data_only=False,
    )

    try:
        sheet = output["测试"]

        assert sheet["A2"].data_type == "f"
        assert sheet["A2"].value == "=1+1"
        assert sheet["A3"].value == "138****5678"

    finally:
        output.close()


def test_mask_rejects_invalid_selection():
    content = make_xlsx()

    with pytest.raises(FileMaskingValidationError):
        mask_file(
            "customers.xlsx",
            content,
            [{
                "sheet_name": "不存在",
                "column_index": 1,
                "sensitive_type": "name",
            }],
        )

    with pytest.raises(FileMaskingValidationError):
        mask_file(
            "customers.xlsx",
            content,
            [
                {
                    "sheet_name": "客户信息",
                    "column_index": 1,
                    "sensitive_type": "name",
                },
                {
                    "sheet_name": "客户信息",
                    "column_index": 1,
                    "sensitive_type": "phone",
                },
            ],
        )
