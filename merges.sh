#!/bin/sh -ve

. ./merges.inc.sh
setup
merge staging
merge production
end
