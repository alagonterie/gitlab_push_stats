# GitLab Push Stats

## Description

This project is dedicated to extracting and analyzing GitLab group members' activity statistics, specifically, focusing on the "push" events. The aim is to derive and provide insights on the average push intervals of different contributors and their longest span of inactivity.

## Usage

1. Enter the parameters such as GitLab URL, private token, and the group ID you wish to analyze.

2. The script extracts active group members excluding those that are explicitly mentioned as exceptions.

3. The script then retrieves all the `push` events from the past determined number of days (default is 365 days, i.e., a year).

4. The average push interval and the longest span are computed for each user.

5. These statistics are then printed and written to the `results.txt` file placed in the same directory as the python script.

## Requirements

- GitLab API (python-gitlab)
- NumPy 

## Note

Please make sure to replace the placeholder for Gitlab API Token and others with actual values.