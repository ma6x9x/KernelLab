# Probes workspace slot

This file is an empty extension point. It is not a probe, and it is not a
code generator.

On a rootless device the directory is:

```
/var/jb/var/kernellab/probes/
```

`postinst` creates that directory. The operator drops their own trees there.
A new test is a file in that folder. It does not require a new KernelLab
`.deb`, and it does not require sideloading a new app build.

KernelLab lists names in that directory. It does not read file bodies, compile
them, or generate them.

A future tool owned by the operator may write into that directory. That tool
is not part of this package. Leave this slot empty in this repo.
