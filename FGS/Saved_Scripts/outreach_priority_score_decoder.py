import pandas as pd
import itertools

# Load the CSV file
file_path = '~/Downloads/table-data (39).csv'  # Update this to your CSV file name in the Downloads folder
data = pd.read_csv(file_path)

# Group data by attribute_name
grouped_data = data.groupby('attribute_name')

# Create a dictionary to hold the grouped data
grouped_dict = {}

for name, group in grouped_data:
    grouped_dict[name] = list(zip(group['operator'], group['value'], group['score']))

# Combine all groups into a list of lists
groups = [grouped_dict[key] for key in grouped_dict]

# Generate all combinations
combinations = list(itertools.product(*groups))

# Prepare data for DataFrame
data_list = []
for combination in combinations:
    row = []
    total_score = 0
    for item in combination:
        operator, value, score = item
        row.append(value)
        row.append(operator)
        row.append(score)
        total_score += score
    row.append(total_score)
    data_list.append(row)

# Define column names with the value column coming before the operator and score columns
columns = []
for attribute in grouped_dict.keys():
    columns.append(attribute + "_value")
    columns.append(attribute + "_operator")
    columns.append(attribute + "_score")
columns.append("total_score")

# Create DataFrame
df = pd.DataFrame(data_list, columns=columns)

# Show the first few rows of the DataFrame
print(df.head())

# Save to CSV if needed
output_file_path = '~/Downloads/combinations_with_scores_and_04_11_new_ltv.csv'  # Specify the output file path
df.to_csv(output_file_path, index=False)