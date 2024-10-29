import pandas as pd

# Read the Excel file into a Pandas DataFrame
df = pd.read_excel("./data/DSS1.xlsx", header=0)

# Print the first few rows of the DataFrame to verify the data was loaded correctly
print(df.head())

# Extract specific columns from the DataFrame (e.g., DMR ID, Closest Gene, etc.)
dmr_id = df["D"]
closest_gene = df["M"]
area = df["Q"]
additional_genes = df["R"]
enhancer_info = df["S"]

# Print the extracted data
print(dmr_id)
print(closest_gene)
print(area)
print(additional_genes)
print(enhancer_info)

# Example usage: filter rows where Area is greater than 0.5
filtered_df = df[df["Q"] > 0.5]
print(filtered_df)
