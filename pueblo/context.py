import platformdirs

pueblo_cache_path = platformdirs.user_cache_path().joinpath("pueblo")
pueblo_cache_path.mkdir(parents=True, exist_ok=True)
