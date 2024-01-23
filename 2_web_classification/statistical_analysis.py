import pandas as pd
import os

# Load the CSV files
file_path1 = 'automated_classification_results.csv'

df = pd.read_csv(file_path1)

# Don't consider basel_stadt, it's incomplete data
df = df[df.canton != 'basel_land']

# Grouping and aggregating
grouped_df = df.groupby(['canton', 'software_name']).agg(
    {
        'page_link': 'count',
        'guide_topic': 'first',
        # **{col: 'max' if col == 'Accessibility Issues' else ('sum' if df[col].dtype == 'int64' else 'any') for col in df.columns if col not in ['page_link', 'canton', 'software_name', 'guide_topic']}
        **{col: ('sum' if df[col].dtype == 'int64' else 'any') for col in df.columns if col not in ['page_link', 'canton', 'software_name', 'guide_topic']}
    }
).reset_index()

grouped_df = grouped_df.rename(columns={'page_link': 'number_of_pages'})

# Export to CSV
# grouped_df.to_csv('grouped_data.csv', index=False, sep=';')

##########

boolean_columns = [
    "Search Function",
    "Hyperlinks",
    "Navigation Menu",
    "Feedback Mechanisms",
    "Instructions Divided into Sections",
    "an Introduction Section",
    "Multilingual Support",
    "a FAQ Section",
    "a Glossary",
    "a Table of Contents",
    "Installation Instructions",
    "an Instructive Example",
]

# Convert certain numerical columns to boolean
columns_to_convert = [
    'Images', 
    'Multimedia Elements', 
    'Interactive Elements', 
    'Accessibility Issues', 
    'Lists/Enumerations', 
    'Tables',
]
for col in columns_to_convert:
    grouped_df[col] = grouped_df[col] > 0

grouped_df['More Pages'] = grouped_df['number_of_pages'] > 1
grouped_df['Long Instructions'] = grouped_df['Content Length'] > 2000
grouped_df['Short Instructions'] = grouped_df['Content Length'] < 300 # https://craftycopy.co.uk/blog/how-long-should-a-web-page-be
grouped_df['Simple Lexicon'] = grouped_df["Low-frequency Jargon"] < 10
grouped_df['Low-frequency Jargon'] = grouped_df["Low-frequency Jargon"] >= 10
extra_columns = ['More Pages', 'Long Instructions', 'Short Instructions', 'Simple Lexicon', 'Low-frequency Jargon']

# Boolean analysis of the converted columns
boolean_converted_stats = pd.DataFrame({
    'Count': grouped_df[columns_to_convert+boolean_columns+extra_columns].sum(),
    'Proportion': grouped_df[columns_to_convert+boolean_columns+extra_columns].mean()*100
})

# Descriptive statistics for 'Content Length' and 'Number of Pages'
content_length_and_pages_stats = grouped_df[['Content Length', 'number_of_pages']].describe()

# Compact visualization of content length and number of pages
content_length_stats = grouped_df['Content Length'].describe().to_frame('Content Length')
number_of_pages_stats = grouped_df['number_of_pages'].describe().to_frame('Number of Pages')
combined_stats = pd.concat([content_length_stats, number_of_pages_stats], axis=1).T

# Output the final tables
print("Boolean Analysis of Selected Features:")
print(boolean_converted_stats)

print("\nCompact Statistics for Content Length and Number of Pages:")
print(combined_stats)