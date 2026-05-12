"""Tests for stdout/stderr capture."""

import sys

from pyrunner.capture import CaptureFixture, CaptureResult


class TestCaptureFixture:

    def test_captures_stdout(self):
        cap = CaptureFixture()
        cap._start()
        try:
            print("hello")
            result = cap.readouterr()
            assert result.out == "hello\n"
            assert result.err == ""
        finally:
            cap.close()

    def test_captures_stderr(self):
        cap = CaptureFixture()
        cap._start()
        try:
            print("error msg", file=sys.stderr)
            result = cap.readouterr()
            assert result.err == "error msg\n"
            assert result.out == ""
        finally:
            cap.close()

    def test_captures_both(self):
        cap = CaptureFixture()
        cap._start()
        try:
            print("out")
            print("err", file=sys.stderr)
            result = cap.readouterr()
            assert result.out == "out\n"
            assert result.err == "err\n"
        finally:
            cap.close()

    def test_readouterr_resets(self):
        cap = CaptureFixture()
        cap._start()
        try:
            print("first")
            cap.readouterr()
            print("second")
            result = cap.readouterr()
            assert result.out == "second\n"
        finally:
            cap.close()

    def test_readouterr_returns_namedtuple(self):
        cap = CaptureFixture()
        cap._start()
        try:
            result = cap.readouterr()
            assert isinstance(result, CaptureResult)
            assert result.out == ""
            assert result.err == ""
        finally:
            cap.close()

    def test_close_restores_streams(self):
        original_out = sys.stdout
        original_err = sys.stderr
        cap = CaptureFixture()
        cap._start()
        assert sys.stdout is not original_out
        assert sys.stderr is not original_err
        cap.close()
        assert sys.stdout is original_out
        assert sys.stderr is original_err

    def test_multiple_writes(self):
        cap = CaptureFixture()
        cap._start()
        try:
            sys.stdout.write("a")
            sys.stdout.write("b")
            sys.stdout.write("c")
            result = cap.readouterr()
            assert result.out == "abc"
        finally:
            cap.close()

    def test_disabled_context_manager(self):
        original_out = sys.stdout
        cap = CaptureFixture()
        cap._start()
        try:
            print("captured")
            with cap.disabled():
                assert sys.stdout is original_out
            assert sys.stdout is not original_out
            result = cap.readouterr()
            assert "captured" in result.out
        finally:
            cap.close()

    def test_disabled_does_not_lose_output(self):
        cap = CaptureFixture()
        cap._start()
        try:
            print("before")
            with cap.disabled():
                pass
            print("after")
            result = cap.readouterr()
            assert "before" in result.out
            assert "after" in result.out
        finally:
            cap.close()

    def test_close_captures_remaining(self):
        cap = CaptureFixture()
        cap._start()
        print("final")
        cap.close()
        result = cap.readouterr()
        assert "final" in result.out

    def test_empty_capture(self):
        cap = CaptureFixture()
        cap._start()
        try:
            result = cap.readouterr()
            assert result.out == ""
            assert result.err == ""
        finally:
            cap.close()

    def test_multiline_output(self):
        cap = CaptureFixture()
        cap._start()
        try:
            print("line1")
            print("line2")
            print("line3")
            result = cap.readouterr()
            assert result.out == "line1\nline2\nline3\n"
        finally:
            cap.close()

    def test_stderr_separate_from_stdout(self):
        cap = CaptureFixture()
        cap._start()
        try:
            print("stdout")
            print("stderr", file=sys.stderr)
            result = cap.readouterr()
            assert "stderr" not in result.out
            assert "stdout" not in result.err
        finally:
            cap.close()

    def test_close_is_idempotent(self):
        cap = CaptureFixture()
        cap._start()
        cap.close()
        cap.close()

    def test_write_with_no_newline(self):
        cap = CaptureFixture()
        cap._start()
        try:
            sys.stdout.write("no newline")
            result = cap.readouterr()
            assert result.out == "no newline"
        finally:
            cap.close()
