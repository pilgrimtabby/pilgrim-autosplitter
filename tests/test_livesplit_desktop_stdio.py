# Copyright (c) 2024-2026 pilgrim_tabby

"""Tests for LiveSplit Desktop stdin/stdout helpers."""

from __future__ import annotations

import os

from livesplit.desktop_stdio import (
    emit_command,
    is_auto_controlled,
    print_handshake,
    strip_auto_controlled_flag,
)


def test_is_auto_controlled_detects_flag():
    assert is_auto_controlled(["prog", "--auto-controlled"]) is True
    assert is_auto_controlled(["prog", "--minimized"]) is False
    assert is_auto_controlled(["prog"]) is False


def test_strip_auto_controlled_flag():
    assert strip_auto_controlled_flag(["a", "--auto-controlled", "b"]) == ["a", "b"]
    assert strip_auto_controlled_flag(["a", "b"]) == ["a", "b"]


def test_print_handshake_writes_version_and_pid(capsys):
    print_handshake("v1.1.3")
    out = capsys.readouterr().out
    lines = out.strip().splitlines()
    assert lines[0] == "v1.1.3"
    assert lines[1] == str(os.getpid())


def test_emit_command_flushes_line(capsys):
    emit_command("split")
    assert capsys.readouterr().out == "split\n"
