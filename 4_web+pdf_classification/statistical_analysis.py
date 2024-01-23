import pandas as pd
import os

# Load the CSV files
file_path1 = '../2_web_classification/automated_classification/automated_classification_results.csv'
file_path2 = '../3_pdf_classification/automated_classification/automated_classification_results.csv'

df1 = pd.read_csv(file_path1)
df2 = pd.read_csv(file_path2)

# Don't consider basel_stadt, it's incomplete data
df1 = df1[df1.canton != 'basel_land']
df2 = df2[df2.canton != 'basel_land']

# Grouping and aggregating
grouped_df1 = df1.groupby(['canton', 'software_name']).agg(
    {
        'page_link': 'count',
        'guide_topic': 'first',  # Assuming you want the first 'guide_topic' per group
        **{col: ('sum' if df1[col].dtype == 'int64' else 'any') for col in df1.columns if col not in ['page_link', 'canton', 'software_name', 'guide_topic']}
    }
).reset_index()
grouped_df1 = grouped_df1.rename(columns={'page_link': 'number_of_pages'})
###########
grouped_df2 = df2.groupby(['canton', 'software_name']).agg(
    {
        'page_link': 'count',
        'guide_topic': 'first',
        # **{col: 'max' if col == 'Accessibility Issues' else ('sum' if df2[col].dtype == 'int64' else 'any') for col in df2.columns if col not in ['page_link', 'canton', 'software_name', 'guide_topic']}
        **{col: ('sum' if df2[col].dtype == 'int64' else 'any') for col in df2.columns if col not in ['page_link', 'canton', 'software_name', 'guide_topic']}
    }
).reset_index()
del grouped_df2['page_link']

grouped_df = pd.concat([grouped_df1, grouped_df2])
grouped_df = grouped_df.groupby(['canton', 'software_name']).agg(
    {
        'guide_topic': 'first',
        **{col: ('sum' if grouped_df[col].dtype == 'int64' else 'any') for col in grouped_df.columns if col not in ['canton', 'software_name', 'guide_topic']}
    }
).reset_index()

print(f'Unique software applications: {len(grouped_df)}')

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

###################################
canton_info = pd.DataFrame({ # Info taken from: https://www.bfs.admin.ch/bfs/en/home/statistics/national-economy/national-accounts/gross-domestic-product-canton.html ; https://www.bfs.admin.ch/bfs/en/home/statistics/population.html
    'Code': ['ZH', 'BE', 'VD', 'GE', 'AG', 'SG', 'BS', 'TI', 'LU', 'BL', 'ZG', 'VS', 'FR', 'SO', 'TG', 'NE', 'GR', 'SZ', 'SH', 'JU', 'AR', 'NW', 'GL', 'OW', 'UR', 'AI'],
    'Name': ['Zürich', 'Bern', 'Vaud', 'Genève', 'Aargau', 'St. Gallen', 'Basel-Stadt', 'Ticino', 'Luzern', 'Basel-Landschaft', 'Zug', 'Valais', 'Fribourg', 'Solothurn', 'Thurgau', 'Neuchâtel', 'Graubünden', 'Schwyz', 'Schaffhausen', 'Jura', 'Appenzell Ausserrhoden', 'Nidwalden', 'Glarus', 'Obwalden', 'Uri', 'Appenzell Innerrhoden'],
    'canton': ['zurich', 'bern', 'vaud', 'geneva', 'aargau', 'st_gallen', 'basel_stadt', 'ticino', 'lucerne', 'basel_land', 'zug', 'valais', 'freiburg', 'solothurn', 'thurgau', 'neuchatel', 'graubunden', 'schwyz', 'schaffhausen', 'jura', 'appenzell_ausserroden', 'nidwalden', 'glarus', 'obwalden', 'uri', 'appenzell_inneroden'],
    # GDP is in million CHF
    'GDP_(2020)': [149209, 80589, 56443, 52016, 44108, 38601, 37706, 29018, 28040, 20464, 20319, 19026, 18886, 18141, 17559, 15320, 14627, 10021, 7242, 4626, 3414, 2866, 2774, 2579, 1982, 1043],
    # GDP per capita is in CHF
    'GDP_per_capita_(2020)': [96491, 77393, 69688, 102954, 63929, 75301, 192092, 82617, 67609, 70513, 158474, 54827, 58357, 65642, 62438, 86951, 73297, 62121, 87546, 62810, 61658, 66192, 68122, 67843, 53910, 64336],
    'Population_(2020)': [1539275, 1039474, 805098, 504128, 685845, 510734, 195844, 351491, 413120, 289468, 127642, 345525, 321783, 275247, 279547, 176496, 199021, 160480, 82348, 73584, 55445, 43087, 40590, 37930, 36703, 16128],
})

###################################
import matplotlib.pyplot as plt
import seaborn as sns

# Count the number of web and PDF guides per canton
web_counts = df1.groupby('canton').count()
pdf_counts = df2.groupby('canton').count()

# Merge these counts with the canton_info dataframe
merged_df = canton_info.set_index('canton').join(web_counts).join(pdf_counts, lsuffix='_web', rsuffix='_pdf')
# Filter out cantons with no links (both web and PDF)
merged_df = merged_df[(merged_df['page_link_web'] > 0) | (merged_df['page_link_pdf'] > 0)]
merged_df.rename(columns={'page_link_web': 'Web', 'page_link_pdf': 'PDF'}, inplace=True)

# Replace NaN with 0
merged_df.fillna(0, inplace=True)

# Order by GDP
merged_df.sort_values('GDP_(2020)', ascending=False, inplace=True)
merged_df.index = merged_df.index.str.replace('_', ' ')

####
# Plot enhancements
colors = sns.color_palette('bright')
fig, ax = plt.subplots(figsize=(12, 9))
merged_df.plot(kind='bar', y=['Web', 'PDF'], stacked=True, ax=ax, color=colors)
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, horizontalalignment='right', fontsize=16)
# ax.set_title('Distribution of Direct/Indirect Software Guides Across Cantons', fontsize=18, weight='bold')
ax.set_xlabel('', fontsize=16, weight='bold')
ax.set_ylabel('Number of Links', fontsize=16, weight='bold')

# Add grid lines
ax.yaxis.grid(True, linestyle='--', which='major', color='grey', alpha=0.6)

# Increase font size of y-axis tick labels
ax.tick_params(axis='y', labelsize=14)

# Increase font size of legend and remove title
ax.legend(title='Guide Format', title_fontsize='16', fontsize='14')
####

# Show plot
plt.tight_layout()
plt.savefig('page_links_by_canton.pdf')


#################################

import textwrap

def wrap_labels(ax, width, break_long_words=False):
    """Wrap labels to multiple lines."""
    labels = []
    for label in ax.get_yticklabels():
        text = label.get_text()
        labels.append(textwrap.fill(text, width=width, break_long_words=break_long_words))
    ax.set_yticklabels(labels, ha='right')

# Combine the dataframes
combined_df = pd.concat([df1, df2])
# combined_df['guide_topic'] = combined_df['guide_topic'].replace('Maps, infrastructures and territorial planning', 'Maps')

combined_df = combined_df.groupby(['canton', 'software_name']).agg({'guide_topic': 'first'}).reset_index()

# Count the number of rows per guide_topic
topic_counts = combined_df['guide_topic'].value_counts().sort_values(ascending=False)

# Plotting
plt.figure(figsize=(8, 7))
sns.barplot(y=topic_counts.index, x=topic_counts.values, palette='coolwarm', orient='h')
# plt.title("Distribution of Guide Topics")
# Wrap the Y-axis labels
ax = plt.gca()
wrap_labels(ax, width=24)  # Adjust 'width' as per your requirement
# Remove the Y-axis label
plt.ylabel('')  # Or plt.gca().set_ylabel('')
sns.despine()
# Increase font size
plt.xticks(fontsize=12)  # Adjust font size for x-axis labels
plt.yticks(fontsize=12)  # Adjust font size for y-axis labels
plt.xlabel("Count")
# Annotating the bars with counts for clarity
for index, value in enumerate(topic_counts.values):
    plt.text(value, index, f' {value}', va='center', fontsize=10)
plt.tight_layout()
plt.savefig('guide_topics_distribution.pdf')