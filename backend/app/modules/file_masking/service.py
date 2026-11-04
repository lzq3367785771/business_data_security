
import csv
import io
import zipfile
import re

from openpyxl import load_workbook

from app.modules.file_masking.detector import detect_column

from openpyxl.cell.cell import MergedCell

from app.modules.file_masking.masking import (
    SUPPORTED_SENSITIVE_TYPES,
    mask_cell_value,
)


MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_SAMPLE_ROWS = 200
MAX_COLUMNS = 200
MAX_XLSX_UNCOMPRESSED_SIZE = 100 * 1024 * 1024
MAX_XLSX_ENTRIES = 5000


class FileMaskingValidationError(ValueError):
    """文件脱敏输入校验异常。"""


def _validate_filename(filename: str) -> str:
    """校验文件名，禁止路径穿越。"""

    if not filename or not isinstance(filename, str):
        raise FileMaskingValidationError("文件名不能为空")

    filename = filename.strip()

    if (
        len(filename) > 255
        or any(x in filename for x in ("/", "\\", "\x00"))
        or filename in {".", ".."}
    ):
        raise FileMaskingValidationError("非法文件名")

    extension = filename.rsplit(".", 1)[-1].lower()

    if extension not in {"csv", "xlsx"}:
        raise FileMaskingValidationError(
            "仅支持 CSV 和 XLSX 文件"
        )

    return extension


def _validate_size(content: bytes):
    if not content:
        raise FileMaskingValidationError("上传文件为空")

    if len(content) > MAX_FILE_SIZE:
        raise FileMaskingValidationError(
            "文件超过 10MB 限制"
        )


def _is_formula(value, data_type=None) -> bool:
    if data_type == "f":
        return True

    return (
        isinstance(value, str)
        and value.lstrip().startswith("=")
    )


def _build_column_result(
    column_name,
    column_index,
    sample_values,
):
    """生成不包含原始数据的字段识别结果。"""

    result = detect_column(
        column_name,
        sample_values,
    )

    return {
        "column_index": column_index,
        "column_name": str(column_name),
        "is_sensitive": result["is_sensitive"],
        "sensitive_type": result["sensitive_type"],
        "sensitive_label": result["sensitive_label"],
        "sensitivity_level": result["sensitivity_level"],
        "detection_method": result["detection_method"],
        "confidence": result["confidence"],
        "sample_count": result["sample_count"],
        "matched_count": result["matched_count"],
        "match_ratio": result["match_ratio"],
        "conflict": result.get("conflict", False),
        "detection_reason": result["detection_reason"],
    }


def _validate_xlsx(content: bytes):
    """验证 XLSX ZIP 结构，限制压缩包展开规模。"""

    stream = io.BytesIO(content)

    if not zipfile.is_zipfile(stream):
        raise FileMaskingValidationError(
            "XLSX 文件格式无效"
        )

    try:
        with zipfile.ZipFile(stream) as archive:
            entries = archive.infolist()

            if len(entries) > MAX_XLSX_ENTRIES:
                raise FileMaskingValidationError(
                    "Excel 文件内部文件数量异常"
                )

            names = set()
            total_size = 0

            for entry in entries:
                name = entry.filename.replace("\\", "/")

                if (
                    name.startswith("/")
                    or ".." in name.split("/")
                    or entry.flag_bits & 0x1
                ):
                    raise FileMaskingValidationError(
                        "Excel 文件包含不安全的压缩内容"
                    )

                if name.lower().endswith("vbaproject.bin"):
                    raise FileMaskingValidationError(
                        "不支持包含宏的 Excel 文件"
                    )

                names.add(name)
                total_size += entry.file_size

            if total_size > MAX_XLSX_UNCOMPRESSED_SIZE:
                raise FileMaskingValidationError(
                    "Excel 文件解压后体积过大"
                )

            if (
                "[Content_Types].xml" not in names
                or "xl/workbook.xml" not in names
            ):
                raise FileMaskingValidationError(
                    "不是有效的 XLSX 工作簿"
                )

    except zipfile.BadZipFile as exc:
        raise FileMaskingValidationError(
            "Excel 文件损坏"
        ) from exc


def _preview_xlsx(content: bytes):
    """解析 XLSX，支持多工作表。"""

    _validate_xlsx(content)

    try:
        workbook = load_workbook(
            io.BytesIO(content),
            read_only=True,
            data_only=False,
            keep_links=False,
        )
    except Exception as exc:
        raise FileMaskingValidationError(
            "Excel 文件无法解析"
        ) from exc

    sheets = []

    try:

        for worksheet in workbook.worksheets:

            # 重置 Excel 内部记录的工作表尺寸
            worksheet.reset_dimensions()

            try:
                # 重新扫描实际单元格，计算真实数据范围
                worksheet.calculate_dimension(force=True)

            except UnboundLocalError:
                # 空工作表没有可计算的单元格，直接跳过
                continue

            max_column = worksheet.max_column or 1
            max_row = worksheet.max_row or 1


            if max_column > MAX_COLUMNS:
                raise FileMaskingValidationError(
                    "工作表列数超过 200 列限制"
                )

            rows = worksheet.iter_rows(
                min_row=1,
                max_row=min(max_row, MAX_SAMPLE_ROWS + 1),
                max_col=max_column,
            )

            header_cells = next(rows, None)

            if not header_cells:
                continue

            if not any(cell.value is not None for cell in header_cells):
                continue

            headers = []

            for index, cell in enumerate(header_cells, start=1):
                value = cell.value

                if _is_formula(value, cell.data_type):
                    value = None

                header = (
                    str(value).strip()
                    if value is not None
                    else f"Column_{index}"
                )

                headers.append(header)

            samples = [[] for _ in headers]
            scanned_rows = 0

            for row in rows:
                scanned_rows += 1

                for index, cell in enumerate(row):
                    if index >= len(samples):
                        break

                    value = cell.value

                    if _is_formula(value, cell.data_type):
                        continue

                    if value is None:
                        continue

                    if isinstance(value, str) and not value.strip():
                        continue

                    samples[index].append(value)

            columns = [
                _build_column_result(
                    header,
                    index,
                    samples[index - 1],
                )
                for index, header in enumerate(headers, start=1)
            ]

            sheets.append({
                "sheet_name": worksheet.title,
                "sampled_rows": scanned_rows,
                "columns": columns,
            })

    finally:
        workbook.close()

    return sheets


def _decode_csv(content: bytes):
    """尝试常见 CSV 编码，避免错误解码。"""

    encodings = []

    if content.startswith(b"\xff\xfe") or content.startswith(b"\xfe\xff"):
        encodings.append("utf-16")
    else:
        encodings.extend([
            "utf-8-sig",
            "utf-8",
            "gb18030",
        ])

    for encoding in encodings:
        try:
            text = content.decode(encoding)

            if "\x00" in text:
                continue

            return text, encoding

        except UnicodeDecodeError:
            continue

    raise FileMaskingValidationError(
        "CSV 文件编码不受支持"
    )


def _preview_csv(content: bytes):
    """解析 CSV 文件。"""

    text, encoding = _decode_csv(content)

    try:
        try:
            dialect = csv.Sniffer().sniff(
                text[:8192],
                delimiters=",\t;|",
            )
        except csv.Error:
            dialect = csv.excel

        reader = csv.reader(
            io.StringIO(text, newline=""),
            dialect,
        )

        headers = next(reader, None)

        if not headers:
            raise FileMaskingValidationError(
                "CSV 文件没有有效表头"
            )

        if len(headers) > MAX_COLUMNS:
            raise FileMaskingValidationError(
                "CSV 列数超过 200 列限制"
            )

        headers = [
            str(value).strip() or f"Column_{index}"
            for index, value in enumerate(headers, start=1)
        ]

        samples = [[] for _ in headers]
        scanned_rows = 0

        for row in reader:
            if scanned_rows >= MAX_SAMPLE_ROWS:
                break

            if len(row) > MAX_COLUMNS:
                raise FileMaskingValidationError(
                    "CSV 数据列数超过限制"
                )

            if len(row) > len(headers) and any(
                str(value).strip()
                for value in row[len(headers):]
            ):
                raise FileMaskingValidationError(
                    "CSV 数据列数与表头不一致"
                )

            scanned_rows += 1

            for index in range(min(len(row), len(headers))):
                value = row[index]

                if not value.strip() or _is_formula(value):
                    continue

                samples[index].append(value)

        columns = [
            _build_column_result(
                header,
                index,
                samples[index - 1],
            )
            for index, header in enumerate(headers, start=1)
        ]

        return [{
            "sheet_name": "CSV",
            "sampled_rows": scanned_rows,
            "columns": columns,
        }], encoding

    except csv.Error as exc:
        raise FileMaskingValidationError(
            "CSV 文件内容无法解析"
        ) from exc


def preview_file(filename: str, content: bytes):
    """
    文件脱敏预览入口。

    不保存文件，不返回原始单元格数据。
    """

    extension = _validate_filename(filename)
    _validate_size(content)

    if extension == "xlsx":
        if not content.startswith(b"PK"):
            raise FileMaskingValidationError(
                "文件内容与 XLSX 扩展名不匹配"
            )

        sheets = _preview_xlsx(content)
        encoding = None

    else:
        if content.startswith(b"PK"):
            raise FileMaskingValidationError(
                "文件内容与 CSV 扩展名不匹配"
            )

        sheets, encoding = _preview_csv(content)

    sensitive_count = sum(
        1
        for sheet in sheets
        for column in sheet["columns"]
        if column["is_sensitive"]
    )

    return {
        "filename": filename,
        "file_type": extension,
        "size_bytes": len(content),
        "encoding": encoding,
        "sheets": sheets,
        "total_sensitive_columns": sensitive_count,
    }



# ==========================================
# M5.2.4 文件实际脱敏与下载
# ==========================================

def _selection_to_dict(selection):
    if isinstance(selection, dict):
        return selection

    if hasattr(selection, "model_dump"):
        return selection.model_dump()

    if hasattr(selection, "dict"):
        return selection.dict()

    raise FileMaskingValidationError("字段选择格式无效")


def _validate_selections(selections, sheet_column_counts):
    if not isinstance(selections, (list, tuple)) or not selections:
        raise FileMaskingValidationError("至少选择一个脱敏字段")

    if len(selections) > 100:
        raise FileMaskingValidationError("一次最多选择100个字段")

    normalized = []
    seen = set()

    for raw in selections:
        item = _selection_to_dict(raw)

        sheet_name = item.get("sheet_name")
        column_index = item.get("column_index")
        sensitive_type = item.get("sensitive_type")

        if not isinstance(sheet_name, str) or not sheet_name.strip():
            raise FileMaskingValidationError("工作表名称不能为空")

        if (
            not isinstance(column_index, int)
            or isinstance(column_index, bool)
            or column_index < 1
            or column_index > 16384
        ):
            raise FileMaskingValidationError("列序号无效")

        if (
            not isinstance(sensitive_type, str)
            or sensitive_type not in SUPPORTED_SENSITIVE_TYPES
        ):
            raise FileMaskingValidationError("不支持的敏感类型")

        key = (sheet_name, column_index)

        if key in seen:
            raise FileMaskingValidationError("同一列不能重复选择")

        seen.add(key)

        if sheet_name not in sheet_column_counts:
            raise FileMaskingValidationError(
                f"工作表不存在：{sheet_name}"
            )

        if column_index > sheet_column_counts[sheet_name]:
            raise FileMaskingValidationError(
                f"列序号超出范围：{sheet_name}"
            )

        normalized.append({
            "sheet_name": sheet_name,
            "column_index": column_index,
            "sensitive_type": sensitive_type,
        })

    return normalized


def _safe_csv_cell(value):
    """防止 CSV 公式注入，同时保留正常负数。"""

    if not isinstance(value, str) or not value:
        return value

    stripped = value.strip()

    if re.fullmatch(
        r"-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",
        stripped,
    ):
        return value

    candidate = value.lstrip(" \t\r\n\x00\x0b\x0c")

    if candidate.startswith(("=", "+", "-", "@")):
        return "'" + value

    return value


def _detect_csv_dialect(text):
    try:
        dialect = csv.Sniffer().sniff(
            text[:8192],
            delimiters=",\t;|",
        )
    except csv.Error:
        dialect = csv.excel

    if "\r\n" in text:
        line_terminator = "\r\n"
    elif "\r" in text and "\n" not in text:
        line_terminator = "\r"
    else:
        line_terminator = "\n"

    return dialect, line_terminator


def _mask_csv(content, selections):
    text, encoding = _decode_csv(content)

    dialect, line_terminator = _detect_csv_dialect(text)

    try:
        reader = csv.reader(
            io.StringIO(text, newline=""),
            dialect,
        )

        rows = list(reader)

    except csv.Error as exc:
        raise FileMaskingValidationError(
            "CSV 文件无法解析"
        ) from exc

    if not rows or not rows[0]:
        raise FileMaskingValidationError("CSV 文件没有有效表头")

    headers = rows[0]

    if len(headers) > MAX_COLUMNS:
        raise FileMaskingValidationError("CSV 列数超过限制")

    for row in rows[1:]:
        if len(row) > MAX_COLUMNS:
            raise FileMaskingValidationError("CSV 数据列数超过限制")

        if len(row) > len(headers) and any(
            str(value).strip()
            for value in row[len(headers):]
        ):
            raise FileMaskingValidationError(
                "CSV 数据列数与表头不一致"
            )

    normalized = _validate_selections(
        selections,
        {"CSV": len(headers)},
    )

    selected_by_column = {
        item["column_index"] - 1: item["sensitive_type"]
        for item in normalized
    }

    output = io.StringIO(newline="")

    writer = csv.writer(
        output,
        dialect=dialect,
        lineterminator=line_terminator,
    )

    writer.writerow([
        _safe_csv_cell(value)
        for value in headers
    ])

    processed_cells = 0

    for row in rows[1:]:
        output_row = list(row)

        for column_index, sensitive_type in selected_by_column.items():

            if column_index >= len(output_row):
                continue

            value = output_row[column_index]

            if _is_formula(value) or value == "":
                continue

            output_row[column_index] = mask_cell_value(
                value,
                sensitive_type,
            )

            processed_cells += 1

        # 所有输出字段均进行 CSV 公式注入防护
        output_row = [
            _safe_csv_cell(value)
            for value in output_row
        ]

        writer.writerow(output_row)

    return (
        output.getvalue().encode(encoding),
        normalized,
        processed_cells,
        encoding,
    )


def _mask_xlsx(content, selections):
    _validate_xlsx(content)

    try:
        workbook = load_workbook(
            io.BytesIO(content),
            read_only=False,
            data_only=False,
            keep_links=True,
        )

    except Exception as exc:
        raise FileMaskingValidationError(
            "Excel 文件无法解析"
        ) from exc

    try:
        sheet_column_counts = {
            worksheet.title: (
                worksheet.max_column or 1
            )
            for worksheet in workbook.worksheets
        }

        if any(
            count > MAX_COLUMNS
            for count in sheet_column_counts.values()
        ):
            raise FileMaskingValidationError(
                "工作表列数超过200列限制"
            )

        normalized = _validate_selections(
            selections,
            sheet_column_counts,
        )

        processed_cells = 0

        for item in normalized:
            worksheet = workbook[item["sheet_name"]]

            column_index = item["column_index"]
            sensitive_type = item["sensitive_type"]

            for row_index in range(
                2,
                (worksheet.max_row or 1) + 1,
            ):

                cell = worksheet.cell(
                    row=row_index,
                    column=column_index,
                )

                if isinstance(cell, MergedCell):
                    continue

                # 公式单元格保持原样
                if (
                    cell.data_type == "f"
                    or _is_formula(cell.value)
                ):
                    continue

                if cell.value is None or cell.value == "":
                    continue

                cell.value = mask_cell_value(
                    cell.value,
                    sensitive_type,
                )

                processed_cells += 1

        output = io.BytesIO()

        workbook.save(output)

        return (
            output.getvalue(),
            normalized,
            processed_cells,
        )

    except FileMaskingValidationError:
        raise

    except Exception as exc:
        raise FileMaskingValidationError(
            "Excel 脱敏处理失败"
        ) from exc

    finally:
        workbook.close()


def mask_file(filename: str, content: bytes, selections):
    """
    文件实际脱敏入口。

    只在内存中生成脱敏副本，不覆盖原文件。
    """

    extension = _validate_filename(filename)

    _validate_size(content)

    if extension == "xlsx":

        if not content.startswith(b"PK"):
            raise FileMaskingValidationError(
                "文件内容与 XLSX 扩展名不匹配"
            )

        output_content, normalized, processed_cells = (
            _mask_xlsx(content, selections)
        )

        media_type = (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )

        encoding = None

    else:

        if content.startswith(b"PK"):
            raise FileMaskingValidationError(
                "文件内容与 CSV 扩展名不匹配"
            )

        (
            output_content,
            normalized,
            processed_cells,
            encoding,
        ) = _mask_csv(content, selections)

        media_type = "text/csv"

    stem = filename.rsplit(".", 1)[0]

    output_filename = f"{stem}_masked.{extension}"

    return {
        "content": output_content,
        "filename": output_filename,
        "media_type": media_type,
        "file_type": extension,
        "original_size": len(content),
        "output_size": len(output_content),
        "processed_cells": processed_cells,
        "encoding": encoding,
        "selections": normalized,
    }
