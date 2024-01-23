import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import json

# Set the option to display all rows and columns (if they are not too large)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

correlation_visibility_threshold = 0.4

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
# prefix = 'Mean N.'

canton_characteristics = ['GDP (2020)', 'GDP per capita (2020)', 'Population (2020)']
features_to_sum = []
features_to_average = [
    'Content Length',
    'Search Function',
    'Images', 
    'Interactive Elements', 
    'Accessibility Issues',
    #####
    'Hyperlinks', 
    'Multimedia Elements', 
    #####
    'Instructions Divided into Sections',
    'Tables',
    'Lists/Enumerations',
    # 'ToC/Nav',
    'a Table of Contents',
    'Navigation Menu',
    'a FAQ Section',
    'a Glossary',
    'an Introduction Section',
    'Installation Instructions',
    'Low-frequency Jargon',
    # 'an Instructive Example',
    'Multilingual Support',
    'Pages',
    'Feedback Mechanisms',
]
webpage_features = features_to_average+features_to_sum

is_video = lambda x: any(k in x.lower() for k in ['video'])
is_static_doc = lambda x: any(k in x.lower() for k in ['pdf','zip','doc'])
is_webpage = lambda x: any(k in x.lower() for k in ['web','online','course'])

# Step 2: Load the CSV files into DataFrames
web_path = '../2_web_classification/automated_classification/automated_classification_results.csv'
pdf_path = '../3_pdf_classification/automated_classification/automated_classification_results.csv'

df_web = pd.read_csv(web_path)
df_pdf = pd.read_csv(pdf_path)

# Append df2_only to df1 and fill missing columns with NaN
df_all = pd.concat([df_web, df_pdf], sort=False)

def build_plot(df, prefix=''):
    # Only get software guides, filter out the rest
    df = df[
        (df['page_is_software_guide'].str.startswith('Yes', na=False)) #|
        # (df['page_contains_software_guide'].str.startswith('Yes', na=False))
    ]
    # Don't consider basel_stadt, it's incomplete data
    df = df[df.canton != 'basel_land']

    unique_cantons = df['canton'].nunique()
    print(f"<{prefix}> There are {len(df)} links from {unique_cantons} cantons")
    print(df['canton'].unique())

    ##############################
    df['guide_topic'] = df['guide_topic'].apply(lambda x: x.strip())
    df['software_name'] = df['software_name'].apply(lambda x: x.lower().strip())

    df['Low-frequency Jargon'] = df['Low-frequency Jargon'].fillna(-1).astype(int)
    df['Images'] = df['Images'].fillna(-1).astype(int)
    df['Tables'] = df['Tables'].fillna(-1).astype(int)
    df['Lists/Enumerations'] = df['Lists/Enumerations'].fillna(-1).astype(int)
    df['Accessibility Issues'] = df['Accessibility Issues'].fillna(-1).astype(int)
    df['Search Function'] = df['Search Function'].fillna(False).astype(bool)
    df['Feedback Mechanisms'] = df['Feedback Mechanisms'].fillna(False).astype(bool)
    df['Multilingual Support'] = df['Multilingual Support'].fillna(False).astype(bool)
    # df['an Instructive Example'] = df['an Instructive Example'].fillna(False).astype(bool)
    df['Multimedia Elements'] = df['Multimedia Elements'].fillna(-1).astype(int)
    df['Interactive Elements'] = df['Interactive Elements'].fillna(-1).astype(int)
    if 'number_of_pages' in df:
        df['number_of_pages'] = df['number_of_pages'].fillna(1).astype(int)
    else:
        df['number_of_pages'] = 1
    df['Pages'] = df['number_of_pages']

    df['Links to Doc/PDF SGs'] = df.apply(
        lambda row: is_static_doc(row['guide_format']),
        axis=1
    ).astype(bool)

    df['Multimedia Elements'] = df.apply(
        lambda row: max(row['Multimedia Elements'], 1 if is_video(row['guide_format']) else 0),
        axis=1
    ).astype(int)

    df['an Instructive Example'] = df.apply(
        lambda row: row['Multimedia Elements']>0 or row['Images']>0,
        axis=1
    ).astype(bool)

    df['ToC/Nav'] = df.apply(
        lambda row: row['a Table of Contents'] or row['Navigation Menu'],
        axis=1
    )

    # df['Interactive Elements + Multimedia'] = df.apply(
    #     lambda row: row['Interactive Elements'] + row['Links to Video SGs'] if row['Interactive Elements'] >= 0 else -1,
    #     axis=1
    # ).astype(int)

    ###############################################################
    #### Merge links about the same software
    ###############################################################

    # Define a custom aggregation function that sums only non-negative values
    def sum_non_negative(series):
        if series.dtype == 'bool':
            return series.any()
        return series[series >= 0].sum() if len(series[series >= 0]) > 0 else -1

    # Group by canton and software_name, count the links, and sum the webpage_features columns
    df = df.groupby(['canton', 'software_name']).agg(
        {'page_link': 'size', **{col: sum_non_negative for col in webpage_features}}
    ).reset_index()

    # Rename the 'page_link' column to 'number_of_links' to reflect the count of links
    df.rename(columns={'page_link': 'number_of_links'}, inplace=True)

    # Ensure that the 'number_of_links' column is integer typed
    df['number_of_links'] = df['number_of_links'].fillna(0).astype(int)

    # Convert all boolean columns to integers
    for col in df.columns:
        if df[col].dtype == 'bool':
            df[col] = df[col].astype(int)

    ###############################################################
    ##### Replace underscores with spaces for better visualization
    ###############################################################
    canton_info.columns = canton_info.columns.str.replace('_', ' ')
    # df.columns = df.columns.str.replace('_', ' ')

    ###############################################################
    ###############################################################

    # Group by 'canton' and apply the custom function to the relevant features
    avg_feature_counts_by_canton = df.groupby('canton')[features_to_average].apply(
        lambda df: df.apply(lambda series: series[series >= 0].mean() if len(series[series >= 0]) > 0 else 0)
    ).reset_index()
    sum_feature_counts_by_canton = df.groupby('canton')[features_to_sum].apply(
        lambda df: df.apply(lambda series: series[series >= 0].sum() if len(series[series >= 0]) > 0 else 0)
    ).reset_index()

    feature_counts_by_canton = sum_feature_counts_by_canton.merge(
        avg_feature_counts_by_canton,
        on='canton',   # merging on the 'canton' column
        how='inner',   # or 'left', 'right', 'outer' depending on your specific needs
    )

    # Merge feature counts with canton_info to get canton characteristics
    merged_features_df = pd.merge(canton_info, feature_counts_by_canton, left_on='canton', right_on='canton', how='left')

    # Remove unavailable cantons
    merged_features_df = merged_features_df.dropna()

    assert unique_cantons == len(merged_features_df)

    ###############################################################
    ###############################################################

    # Scatter plots
    fig, axes = plt.subplots(len(canton_characteristics), len(webpage_features), figsize=(len(webpage_features)*4+2, len(canton_characteristics)*4))
    for i, canton_char in enumerate(canton_characteristics):
        # Find the canton with the lowest income, highest income, and highest number of links
        lowest_income_canton = merged_features_df.loc[merged_features_df[canton_char].idxmin()]['canton']
        highest_income_canton = merged_features_df.loc[merged_features_df[canton_char].idxmax()]['canton']
        for j, webpage_feature in enumerate(webpage_features):
            ax = axes[i, j]
            sns.scatterplot(x=canton_char, y=webpage_feature, data=merged_features_df, ax=ax)
            ax.set_title(f'{canton_char} vs {webpage_feature}')
            highest_links_canton = merged_features_df.loc[merged_features_df[webpage_feature].idxmax()]['canton']
            # Add labels for Bern, Zurich, and special cases
            for canton in ['bern', lowest_income_canton, highest_income_canton, highest_links_canton]:
                data_point = merged_features_df[merged_features_df['canton'] == canton]
                ax.annotate(canton, (data_point[canton_char].values[0], data_point[webpage_feature].values[0]), textcoords="offset points", xytext=(0,10), ha='center')

    plt.tight_layout()
    plt.savefig(f'scatter_guides_{prefix}.pdf')

    ###############################################################
    ###############################################################

    # Check for constant or NaN columns
    filtered_webpage_features = []
    for col in webpage_features:
        unique_values = merged_features_df[col].nunique()
        nan_values = merged_features_df[col].isna().sum()
        # assert not (unique_values == 1 or nan_values > 0), f"Column '{col}' has {unique_values} unique values and {nan_values} NaN values."
        if not (unique_values == 1 or nan_values > 0):
            filtered_webpage_features.append(col)


    # Calculate Spearman's correlation coefficients and p-values
    correlation_spearman = merged_features_df[canton_characteristics + filtered_webpage_features].corr(method='spearman')
    p_values = merged_features_df[canton_characteristics + filtered_webpage_features].apply(lambda x: merged_features_df[canton_characteristics + filtered_webpage_features].apply(lambda y: stats.spearmanr(x, y)[1]))

    # Use '*' to denote correlations that are statistically significant
    annotations = correlation_spearman.apply(lambda x: x.apply(lambda y: '{:.2f}'.format(y)))
    annotations = annotations.where(p_values > 0.05, annotations + "\n" + p_values.apply(lambda x: x.apply(lambda y: '(p={:.3f})'.format(y))))

    # Filter columns where at least one correlation with canton_characteristics is greater than 0.3
    significant_columns = correlation_spearman.loc[canton_characteristics, filtered_webpage_features].columns[
        (correlation_spearman.loc[canton_characteristics, filtered_webpage_features].abs() > correlation_visibility_threshold).any()
    ]

    plt.figure(figsize=(len(significant_columns)*1.5+2, len(canton_characteristics)*1.5))
    sns.heatmap(correlation_spearman.loc[canton_characteristics, significant_columns], annot=annotations.loc[canton_characteristics, significant_columns], cmap='coolwarm', fmt='s', vmin=-1, vmax=1, center=0)
    # plt.title('Spearman Correlation Heatmap with Significant P-values')
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    plt.savefig(f'heatmap_guides_{prefix}.pdf')

build_plot(df_web, prefix='web')
build_plot(df_pdf, prefix='pdf')
build_plot(df_all, prefix='all')