import pandas as pd

# Read the Excel file into a Pandas DataFrame
df = pd.read_excel("./data/DSS1.xlsx", header=1)  # Adjust the header parameter as needed

# Print the first few rows of the DataFrame to verify the data was loaded correctly
print(df.head())

# Print the column names to verify they match your expectations
print("Column names:", df.columns)

# Extract specific columns from the DataFrame (e.g., DMR ID, Closest Gene, etc.)
# Ensure the column names match exactly with those in the DataFrame
dmr_id = df["DMR ID"]  # Use the exact column name as printed
closest_gene = df["Closest Gene"]
area = df["Area"]
additional_genes = df["Additional Genes"]
enhancer_info = df["ENCODE Promoter Interaction (BingRen Lab)"]

# Print the extracted data
print(dmr_id)
print(closest_gene)
print(area)
print(additional_genes)
print(enhancer_info)

# Example usage: filter rows where Area is greater than 0.5
filtered_df = df[df["Q"] > 0.5]
print(filtered_df)
