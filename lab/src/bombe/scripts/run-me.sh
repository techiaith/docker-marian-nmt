#!/bin/bash

# Run the pipeline from start to finish, in a new session

session="python -m bombe.cli session"
task="python -m bombe.cli tasks"

$session new
$task download-data $(cat unclassified_source_data_links.txt)
$task export-and-clean
$task split-corpus
$task train
$session end


