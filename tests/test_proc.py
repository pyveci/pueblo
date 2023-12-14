import pytest

proc = pytest.importorskip("pueblo.util.proc")
process = proc.process


def test_process_success(tmp_path):
    outfile = tmp_path / "myfile.out.log"
    with process(["echo", "Hello, world."], stdout=open(outfile, "w")) as proc:
        assert isinstance(proc.pid, int)

    with open(outfile, "r") as fp:
        assert fp.read() == "Hello, world.\n"


def test_process_noop():
    process(["mycommand", "myarg", "--myoption", "myoptionvalue"])


def test_process_failure_command_not_found():
    with pytest.raises(FileNotFoundError) as ex:
        with process(["mycommand", "myarg", "--myoption", "myoptionvalue"]):
            pass
    assert ex.match("No such file or directory")


def test_process_failure_in_contextmanager():
    with pytest.raises(ZeroDivisionError):
        with process(["echo", "Hello, world."]) as proc:
            print(proc.pid)  # noqa: T201
            # Even though this throws an exception, the `process` contextmanager
            # will *still* clean up the process correctly.
            0 / 0  # noqa: B018
