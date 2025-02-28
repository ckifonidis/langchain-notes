# Role
You are a senior AI engineer. Your task is to create a python script based on the following functional requirements

# Functional requirements
1. Read one csv a time from the output directory.
2. Decide what the csv describes. There are the following cases: Database description, Tables Description, Sample data, and Other. If the csv is different from Tables Description proceed to the next one. To decide what a csv describes as an AT api. In tables descriptions, each csv row represents a table column and each csv column represents some kind of information on the table column. The information that it represents it is usually the csv column header
3. the results of the processing should be outputted in the same output directory with the _analysis.txt suffix.