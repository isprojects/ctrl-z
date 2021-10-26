#!/bin/bash
createuser ctrlz -U postgres -d
createdb ctrlz -U ctrlz
createdb ctrlz2 -U ctrlz

# when developing locally use
# [creatuser/createdb] ctrlz -U ctrlz -h localhost
