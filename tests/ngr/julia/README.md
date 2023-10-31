# Julia Test Runner

## About
[Pkg] is [Julia]'s built-in package manager.

## Synopsis
```shell
ngr test tests/ngr/julia
```

## What's inside
This folder contains a minimal project to satisfy `Pkg.build()` and `Pkg.test()`.
- https://pkgdocs.julialang.org/v1/creating-packages/

## Backlog

### CI++
Improve CI configuration, to also expand to Dependabot-like functionality.
- https://github.com/julia-actions
- https://github.com/JuliaRegistries/CompatHelper.jl/tree/master/.github/workflows
- https://juliaregistries.github.io/CompatHelper.jl/
- https://github.com/v-i-s-h/Runner.jl/blob/master/.github/workflows/CompatHelper.yml


[Julia]: https://julialang.org/
[Pkg]: https://pkgdocs.julialang.org/
