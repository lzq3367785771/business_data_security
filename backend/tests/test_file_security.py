import pytest

from app.infrastructure.crypto import (
    decrypt_file_bytes,
    encrypt_file_bytes,
)


def test_file_bytes_should_encrypt_and_restore():
    original = (
        b"Business Data Security "
        b"Mini V1 Test File"
    )


    encrypted = (
        encrypt_file_bytes(
            original
        )
    )


    assert encrypted != original

    assert isinstance(
        encrypted,
        bytes,
    )


    restored = (
        decrypt_file_bytes(
            encrypted
        )
    )


    assert restored == original



    


def test_invalid_file_ciphertext_should_fail():

    with pytest.raises(
        ValueError,
        match="文件解密失败",
    ):
        decrypt_file_bytes(
            b"invalid-ciphertext"
        )


from app.modules.file_security.service import (
    build_secure_file,
    restore_secure_file,
)


def test_secure_file_package_should_restore_original_file():

    original = (
        b"This is a Mini V1 "
        b"business security file."
    )


    encrypted = (
        build_secure_file(
            filename="report.txt",
            content_type="text/plain",
            data=original,
        )
    )


    assert encrypted != original


    restored = (
        restore_secure_file(
            encrypted
        )
    )


    assert (
        restored["filename"]
        == "report.txt"
    )

    assert (
        restored["content_type"]
        == "text/plain"
    )

    assert (
        restored["size"]
        == len(original)
    )

    assert (
        restored["data"]
        == original
    )

    assert len(
        restored["sha256"]
    ) == 64


def test_secure_file_should_remove_client_path():

    original = (
        b"test-content"
    )


    encrypted = (
        build_secure_file(
            filename=(
                "../../secret/report.txt"
            ),
            content_type="text/plain",
            data=original,
        )
    )


    restored = (
        restore_secure_file(
            encrypted
        )
    )


    assert (
        restored["filename"]
        == "report.txt"
    )