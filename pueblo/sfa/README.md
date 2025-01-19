# Single File Applications (sfa)


## About

Single File Applications, a few [DWIM] conventions and tools to
install and invoke Python applications defined within single files.


## Preamble

Because, how to invoke an arbitrary Python entrypoint interactively?
```shell
python -m tests.testdata.folder.dummy -c "main()"
python -c "from tests.testdata.folder.dummy import main; main()"
```
Remark: The first command looks good, but does not work, because
each option `-m` and `-c` terminates the option list, so they can
not be used together.


## Synopsis

```shell
# Invoke Python entrypoint with given specification.
PYTHONPATH=$(pwd) sfa run tests.testdata.entrypoint:main
sfa run tests/testdata/entrypoint.py:main
sfa run https://github.com/pyveci/pueblo/raw/refs/heads/main/tests/sfa/basic.py#main
sfa run github://pyveci:pueblo@/tests/testdata/entrypoint.py#main
```


[DWIM]: https://en.wikipedia.org/wiki/DWIM
