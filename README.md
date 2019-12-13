## What?

This extension contacts Phabricator, downloads patch specidied by it's id in `HG_PHAB_DIFF` environment variable, and transparently applies it on top of current head.

## Why?

This was created to work-around lack of proper integration between phabricator, arcanist and Jenkins.
