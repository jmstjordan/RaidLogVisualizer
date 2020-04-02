# Wow Classic DPS Raid Visualizer

## Introduction

This is a simple script that uses classic.warcraftlogs.com's raid logs and builds a nice
data set that can be used for a bar-chart-race visualization found [here](https://observablehq.com/@jmstjordan/bar-chart-race).

If you would like to see the data from your logs, you can fork that observable project, and upload the csv generated from this project to the website.

## Usage

First set an environment variable to your public API Key. This can be found after making an account at warcraftlogs.com.

```sh
export WOW_API_KEY=YOUR_KEY_HERE
```

Then, run the script (requires python 3)

```sh
python raid.py <EventCodeOfRaid>
```

Keep in mind that you will need to have already uploaded your raid logs manually. This project simply enhances the visualizations already provided by warcraftlogs.com
