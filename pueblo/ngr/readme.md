# Next Generation Runner (ngr)


## About

A universal (test) runner program.


## Synopsis

```shell
# Invoke test suite in given directory.
ngr test tests/ngr/make
ngr test tests/ngr/php
ngr test tests/ngr/rust
```


## Etymology

> We finally added a universal test runner, which is effectively just wrapping
> a few other calls, to be able to start maintaining a concise incantation syntax
> across different CI recipes.
>
> - Written in Python.
> - Aims to be reasonably generic and polyglot.
> - Does not assume it is invoked on any kind of CI system.
> - [DWIM]: Mirrors incantation style and invocation experience between CI systems vs.
>   developer sandbox operations, significantly reducing administration overhead.
>   Developers can easily run the same CI recipes without many efforts.
> 
> -- [Introduce universal test runner]

> `ngr.py` originally has been incubated at [cratedb-examples], now it was refactored to a
> standalone package, `pueblo.ngr`, after a few iterations. If you like the idea, it can
> be re-used on other projects, for example on [crate-qa] or others.
> 
> -- [Use universal test runner everywhere]


## Prior Art

- https://github.com/facebookincubator/ptr


## Backlog

- Use PKGX

  Invoke any type of application using any kind of runtime.
  What about Docker or Podman for others?

  - https://pkgx.sh/
  - https://pkgx.dev/

- Look at https://pypi.org/project/ur/.


[crate-qa]: https://github.com/crate/crate-qa
[cratedb-examples]: https://github.com/crate/cratedb-examples
[DWIM]: https://en.wikipedia.org/wiki/DWIM
[Introduce universal test runner]: https://github.com/crate/cratedb-examples/pull/64#pullrequestreview-1702806663
[Source]: https://github.com/crate/cratedb-examples/pull/64#pullrequestreview-1702806663
[Use universal test runner everywhere]: https://github.com/crate/cratedb-examples/pull/96
