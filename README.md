[![codecov](https://codecov.io/gh/trassir/hg-phabdiff/branch/master/graph/badge.svg)](https://codecov.io/gh/trassir/hg-phabdiff)
[![Build Status](https://travis-ci.com/trassir/hg-phabdiff.svg?branch=master)](https://travis-ci.com/trassir/hg-phabdiff)
[![Build status](https://ci.appveyor.com/api/projects/status/9almrajywadddxub/branch/master?svg=true)](https://ci.appveyor.com/project/trassir/hg-phabdiff/branch/master)

## What?

This extension contacts phabricator, downloads patch specified by its id in `HG_PHAB_DIFF` environment variable, and transparently applies it on top of current head.

## Why?

This was created to workaround the lack of proper integration between phabricator, Arcanist and Jenkins.
