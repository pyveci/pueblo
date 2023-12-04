# Next Generation Runner (ngr)


## About

A universal (test) runner program.


## Synopsis

```shell
# Invoke test suite in given directory.
ngr test tests/ngr/elixir
ngr test tests/ngr/julia
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

- Add Golang, Julia, Elixir, Haskell, Zig

- Directly run on repository URL

  `ngr test https://github.com/crate/mongodb-cratedb-migration-tool@develop`
  `ngr test https://github.com/crate/cratedb-prometheus-adapter`

- Use PKGX

  Invoke any type of application using any kind of runtime.
  What about Docker or Podman for others?

  - https://pkgx.sh/
  - https://pkgx.dev/

- Look at https://pypi.org/project/ur/.

- Use Chainguard OCI Images

  - https://github.com/chainguard-images/images
  - https://edu.chainguard.dev/chainguard/chainguard-images/reference/

  ```
  docker run --rm -it cgr.dev/chainguard/bash 'bash --version'
  docker run --rm -it cgr.dev/chainguard/deno --version
  docker run --rm -it cgr.dev/chainguard/go version
  docker run --rm -it cgr.dev/chainguard/gradle --version
  docker run --rm -it cgr.dev/chainguard/jdk java --version
  docker run --rm -it cgr.dev/chainguard/maven --version
  docker run --rm -it cgr.dev/chainguard/node --version
  docker run --rm -it cgr.dev/chainguard/php --version
  docker run --rm -it cgr.dev/chainguard/python --version
  docker run --rm -it cgr.dev/chainguard/ruby --version
  docker run --rm -it cgr.dev/chainguard/rust --version
  ```


[crate-qa]: https://github.com/crate/crate-qa
[cratedb-examples]: https://github.com/crate/cratedb-examples
[DWIM]: https://en.wikipedia.org/wiki/DWIM
[Introduce universal test runner]: https://github.com/crate/cratedb-examples/pull/64#pullrequestreview-1702806663
[Source]: https://github.com/crate/cratedb-examples/pull/64#pullrequestreview-1702806663
[Use universal test runner everywhere]: https://github.com/crate/cratedb-examples/pull/96
