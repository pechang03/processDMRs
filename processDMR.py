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

# Extract specific columns from the DataFrame using the correct column names
dmr_id = df["DMR1"]  # Column for DMR ID
closest_gene = df["Rgs20"]  # Column for the closest gene
area = df["Area"]  # Column for the area statistic
additional_genes = df["Additional Genes"]  # Column for additional genes
enhancer_info = df["Enhancer Info"]  # Column for enhancer information

# Print the extracted data
print("DMR IDs:")
print(dmr_id)
print("Closest Genes:")
print(closest_gene)
print("Area:")
print(area)
print("Additional Genes:")
print(additional_genes)
print("Enhancer Info:")
print(enhancer_info)

# Example usage: filter rows where Area is greater than 0.5
filtered_df = df[df["Area"] > 0.5]
print("Filtered DataFrame:")
print(filtered_df)
