import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr
import numpy as np

import textwrap

def wrap_labels(ax, width, break_long_words=False):
    """Wrap labels to multiple lines."""
    labels = []
    for label in ax.get_yticklabels():
        text = label.get_text()
        labels.append(textwrap.fill(text, width=width, break_long_words=break_long_words))
    ax.set_yticklabels(labels, ha='right')

# Set the option to display all rows and columns (if they are not too large)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


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

# Load the CSV file into a DataFrame
file_path = '../corrected_guide_identification_analysis.csv'
df = pd.read_csv(file_path, delimiter=',')

# Don't consider basel_stadt, it's incomplete data
df = df[df.canton != 'basel_land']

# Filter the DataFrame to only include relevant rows
filtered_link_analysis = df[df['page_is_software_guide'].str.startswith('Yes', na=False) | df['page_contains_software_guide'].str.startswith('Yes', na=False)]

filtered_link_analysis['guide_topic'] = filtered_link_analysis['guide_topic'].apply(lambda x: x.strip())
filtered_link_analysis['software_name'] = filtered_link_analysis['software_name'].apply(lambda x: x.lower().strip())

# Normalize the guide_format column
filtered_link_analysis['guide_format'].fillna('', inplace=True)
filtered_link_analysis['guide_format'] = filtered_link_analysis['guide_format'].apply(lambda x: 'Doc/PDF' if any(k in x.lower() for k in ['pdf','zip','doc']) else x)
filtered_link_analysis['guide_format'] = filtered_link_analysis['guide_format'].apply(lambda x: 'Web' if any(k in x.lower() for k in ['video','audio']) else x)
filtered_link_analysis['guide_format'] = filtered_link_analysis['guide_format'].apply(lambda x: 'Web' if any(k in x.lower() for k in ['web','online','course']) else x)
filtered_link_analysis['guide_format'] = filtered_link_analysis['guide_format'].apply(lambda x: 'Other' if x not in ['Web','Doc/PDF','Video'] else x)

# Generate summary statistics for guide_topic
# Group by canton and software_name, count the links, and sum the webpage_features columns
guide_topic_stats = filtered_link_analysis.groupby(['canton', 'software_name']).agg(
    {'page_link': 'size', 'guide_topic': lambda x: np.array(x)[0]}
).reset_index()
# print(guide_topic_stats)

# Rename the 'page_link' column to 'number_of_links' to reflect the count of links
guide_topic_stats.rename(columns={'page_link': 'number_of_links'}, inplace=True)

# Ensure that the 'number_of_links' column is integer typed
guide_topic_stats['number_of_links'] = guide_topic_stats['number_of_links'].fillna(0).astype(int)
guide_topic_stats = guide_topic_stats['guide_topic'].value_counts().reset_index()
guide_topic_stats.columns = ['Guide Topic', 'Count']

# Generate summary statistics for guide_format
guide_format_stats = filtered_link_analysis[filtered_link_analysis['page_contains_software_guide'].str.startswith('Yes', na=False)]
guide_format_stats = guide_format_stats['guide_format'].value_counts().reset_index()
guide_format_stats.columns = ['Guide Format', 'Count']

# Count the number of links that are software guides or refer to them for each canton
canton_link_count = filtered_link_analysis['canton'].value_counts().reset_index()
canton_link_count.columns = ['canton', 'count_links']

# Merge with canton_info to get wealth and population information
canton_link_count = canton_link_count.merge(canton_info, left_on='canton', right_on='canton')

# Correlation and p-values analysis
correlations = {}
p_values = {}

for feature in ['GDP_(2020)', 'GDP_per_capita_(2020)', 'Population_(2020)']:
    corr, p_val = spearmanr(canton_link_count['count_links'], canton_link_count[feature])
    correlations[feature] = corr
    p_values[feature] = p_val

correlations_df = pd.DataFrame(list(correlations.items()), columns=['Feature', 'Spearman Correlation'])
p_values_df = pd.DataFrame(list(p_values.items()), columns=['Feature', 'P-value'])

# Combine the two dataframes
combined_df = correlations_df.merge(p_values_df, on='Feature')

# Format the annotations
combined_df['Annotation'] = combined_df.apply(lambda row: f"{row['Spearman Correlation']:.2f}" + (f"\n(p={row['P-value']:.4f})" if row['P-value'] < 0.05 else ''), axis=1)

# Rename the 'Feature' column values to remove underscores and rename the 'Spearman Correlation' column
correlations_df['Feature'] = correlations_df['Feature'].str.replace('_', ' ')
correlations_df.rename(columns={'Spearman Correlation': 'Number of Guides Links'}, inplace=True)

# Set 'Feature' as the index
correlations_df.set_index('Feature', inplace=True)

# Generate the heatmap
plt.figure(figsize=(8, 6))
sns.heatmap(correlations_df, annot=combined_df[['Annotation']], cmap='coolwarm', fmt="", vmin=-1, vmax=1, center=0, cbar_kws={'label': 'Spearman Correlation'})
# plt.title('Spearman Correlation Heatmap')
plt.xlabel('')
plt.ylabel('')

plt.tight_layout()
plt.savefig('correlation.png')

# Plot for different guide_topics
guide_topic_stats['Guide Topic'] = guide_topic_stats['Guide Topic'].replace('Maps, infrastructures and territorial planning', 'Maps')
plt.figure(figsize=(10, 6))
sns.barplot(data=guide_topic_stats, x='Count', y='Guide Topic')
# Wrap the Y-axis labels
ax = plt.gca()
wrap_labels(ax, width=24)  # Adjust 'width' as per your requirement
# Remove the Y-axis label
plt.ylabel('')  # Or plt.gca().set_ylabel('')
sns.despine()
# Increase font size
plt.xticks(fontsize=12)  # Adjust font size for x-axis labels
plt.yticks(fontsize=12)  # Adjust font size for y-axis labels
plt.tight_layout()
plt.savefig('Guide_Topics_Distribution.png')

# Plot for different guide_formats
plt.figure(figsize=(10, 6))
sns.barplot(data=guide_format_stats, x='Count', y='Guide Format')
plt.title('Distribution of Different Guide Formats')
plt.tight_layout()
plt.savefig('Guide_Formats_Distribution.png')

# Scatter plot for number of links vs GDP for each canton
plt.figure(figsize=(10, 6))
sns.scatterplot(data=canton_link_count, x='GDP_(2020)', y='count_links')
plt.title('Number of Links vs GDP for Each Canton')

# Find the canton with the lowest income, highest income, and highest number of links
lowest_income_canton = canton_link_count.loc[canton_link_count['GDP_(2020)'].idxmin()]['canton']
highest_income_canton = canton_link_count.loc[canton_link_count['GDP_(2020)'].idxmax()]['canton']
highest_links_canton = canton_link_count.loc[canton_link_count['count_links'].idxmax()]['canton']

# Add labels for Bern, Zurich, and special cases
for canton in ['bern', lowest_income_canton, highest_income_canton, highest_links_canton]:
    data_point = canton_link_count[canton_link_count['canton'] == canton]
    plt.annotate(canton, (data_point['GDP_(2020)'].values[0], data_point['count_links'].values[0]), textcoords="offset points", xytext=(0,10), ha='center')

plt.tight_layout()
plt.savefig('Links_vs_GDP.png')

print('Guide Topic Stats:', guide_topic_stats)
print('Guide Format Stats:', guide_format_stats)
print('Correlations:', correlations_df)
print('page_is_software_guide', len(df[df['page_is_software_guide'].str.startswith('Yes', na=False)]))
print('page_contains_software_guide', len(df[df['page_contains_software_guide'].str.startswith('Yes', na=False)]))
print('page_is_software_guide and page_contains_software_guide', len(df[df['page_is_software_guide'].str.startswith('Yes', na=False) & df['page_contains_software_guide'].str.startswith('Yes', na=False)]))
print('~page_is_software_guide and page_contains_software_guide', len(df[~df['page_is_software_guide'].str.startswith('Yes', na=False) & df['page_contains_software_guide'].str.startswith('Yes', na=False)]))

# Count the number of different guide topics (considered as guide_type here) for each canton
canton_guide_type_count = filtered_link_analysis.groupby('canton')['guide_topic'].nunique().reset_index(name='count_unique_guide_types')

# Merge with canton_info to get wealth information
canton_guide_type_count = canton_guide_type_count.merge(canton_info, left_on='canton', right_on='canton')

# Sort cantons by wealth (GDP in 2020, in million CHF)
canton_guide_type_count = canton_guide_type_count.sort_values(by='GDP_(2020)', ascending=False)

# Plotting
plt.figure(figsize=(15, 8))
sns.barplot(data=canton_guide_type_count, x='Name', y='count_unique_guide_types', palette='viridis')
plt.title('Number of Different Guide Types by Canton (Ordered by Wealth)')
plt.xticks(rotation=45)
plt.xlabel('Canton')
plt.ylabel('Number of Different Guide Types')
plt.tight_layout()
plt.savefig('guide_types_by_canton.png')

canton_guide_type_count[['Name', 'count_unique_guide_types']]

# Correlation analysis for the number of different guide types with canton characteristics
correlations_guide_types = {}
for feature in ['GDP_(2020)', 'GDP_per_capita_(2020)', 'Population_(2020)']:
    corr, _ = spearmanr(canton_guide_type_count['count_unique_guide_types'], canton_guide_type_count[feature])
    correlations_guide_types[feature] = corr

correlations_guide_types_df = pd.DataFrame(list(correlations_guide_types.items()), columns=['Feature', 'Spearman Correlation'])

# Filter and group the data
canton_link_count = filtered_link_analysis.groupby(['canton', 'page_is_software_guide']).size().reset_index(name='count')

# Map 'Yes'/'No' to 'Direct'/'Indirect'
canton_link_count['page_is_software_guide'] = canton_link_count['page_is_software_guide'].map({'Yes': 'Direct', 'No': 'Indirect'})

# Pivot the data for stacked bar plot
canton_link_pivot = canton_link_count.pivot(index='canton', columns='page_is_software_guide', values='count').fillna(0)

# Sort by canton wealth
canton_link_pivot = canton_link_pivot.merge(canton_info, left_on='canton', right_on='canton')
canton_link_pivot = canton_link_pivot.sort_values(by='GDP_(2020)', ascending=False)
canton_link_pivot.set_index('canton', inplace=True)

# Replace underscores with whitespaces in canton names
canton_link_pivot.index = canton_link_pivot.index.str.replace('_', ' ')

# Plot enhancements
colors = sns.color_palette('bright')
fig, ax = plt.subplots(figsize=(12, 9))
canton_link_pivot[['Direct', 'Indirect']].plot(kind='bar', stacked=True, ax=ax, color=colors)
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, horizontalalignment='right', fontsize=16)
# ax.set_title('Distribution of Direct/Indirect Software Guides Across Cantons', fontsize=18, weight='bold')
ax.set_xlabel('', fontsize=16, weight='bold')
ax.set_ylabel('Number of Links', fontsize=16, weight='bold')

# Add grid lines
ax.yaxis.grid(True, linestyle='--', which='major', color='grey', alpha=0.6)

# Increase font size of y-axis tick labels
ax.tick_params(axis='y', labelsize=14)

# Increase font size of legend and remove title
ax.legend(title='Software Guide Type', title_fontsize='16', fontsize='14')

plt.tight_layout()
plt.savefig('page_links_by_canton.png')