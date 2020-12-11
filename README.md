# Dark Chess

This is the repo for Dark Chess, a web implementation of the eponymous variant,
in which you only have vision of what you can attack.

## Attributions/Citations/Etc.

In several places this application makes use of snippets of code from Miguel
Grinberg's "microblog" application (Copyright (c) 2017 Miguel Grinberg, MIT
License). A copy of the source can be found
[here](https://github.com/miguelgrinberg/microblog).

When usage consists of more than a line or two of code, an inline remark is
made indicating so. For what it's worth, all code used could have been
rewritten in such a way as to avoid having to cite the source, but I found no
reason to reinvent the wheel for basic topics like token authorization and
error handling, Miguel has done a good enough job of that himself,
Additionally, the "microblog" application and the "Flask Mega Tutorial" is
where I first learned how to build a practical application with Flask, so it
stands to reason that I would make use of some of the same patterns.