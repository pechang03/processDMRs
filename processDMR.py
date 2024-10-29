import pandas as pd

# Read the Excel file into a Pandas DataFrame
df = pd.read_excel("./data/DSS1.xlsx", header=None)  # Start with no header to inspect the data

# Print the first few rows to understand the structure
print(df.head(10))

# Based on the output, determine the correct header row and adjust the header parameter
# For example, if the actual headers are in the second row, use header=1
df = pd.read_excel("./data/DSS1.xlsx", header=1)  # Adjust this based on your inspection

# Print the column names to verify they match your expectations
print("Column names:", df.columns)

# Extract specific columns from the DataFrame
# Ensure the column names match exactly with those in the DataFrame
dmr_id = df["DMR1"]  # Use the exact column name as printed
closest_gene = df["Rgs20"]  # Adjust based on actual column names
area = df[179.10177964248]  # Adjust based on actual column names
additional_genes = df["Oprk1/e4"]  # Adjust based on actual column names
enhancer_info = df["."]  # Adjust based on actual column names

# Print the extracted data
print(dmr_id)
print(closest_gene)
print(area)
print(additional_genes)
print(enhancer_info)

# Example usage: filter rows where Area is greater than 0.5
filtered_df = df[df[179.10177964248] > 0.5]  # Adjust based on actual column names
print(filtered_df)
