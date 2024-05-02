## Tools caches

During regular operation of the action server, it uses `rcc`, to manage
environments, which in turn uses other tools (such as `micromamba`, `pip` or `uv`)
and each of those tools can create caches so that rebuilding an environment
is faster (so, for instance, if some library as `playwright` is downloaded
once, asking for the same version a second time will not need to redownload it).

These caches are great in general on a developers machine, but when doing an
actual deployment where the `package.yaml` will be static and the same environment
will be used over and over again, such cache files are not needed and they can
waste precious space.

Given that, the action server has a command:

`action-server env clean-tools-caches`

Which can be used to remove such caches (while still keeping all of the existing
environments in place).

Note that if a new environment is requested (which is the case when the 
`package.yaml` contents change or a new package is imported), then the
caches will be rebuilt (and the command to clean the caches would need to
be called again). 

