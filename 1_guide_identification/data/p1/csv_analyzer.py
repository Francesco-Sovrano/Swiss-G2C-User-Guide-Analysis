import zipfile
import os

# Define the path to the uploaded zip file and the directory where it will be unzipped
zip_file_path = 'Archive.zip'
unzip_dir_path = 'unzipped_files/'

# Create the directory if it doesn't exist
if not os.path.exists(unzip_dir_path):
    os.makedirs(unzip_dir_path)

# Unzip the file
with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    zip_ref.extractall(unzip_dir_path)

# List the contents of the unzipped directory
unzipped_contents = os.listdir(unzip_dir_path)

# Initialize a list to hold the names of files that cause errors
error_files = []

# Loop through each folder and read the CSV files
for folder in unzipped_contents:
    # Skip the __MACOSX folder
    if folder == '__MACOSX':
        continue
    
    folder_path = os.path.join(unzip_dir_path, folder)
    
    # Loop through each file in the folder
    for file_name in os.listdir(folder_path):
        # Skip system files like .DS_Store
        if file_name.endswith('.csv'):
            file_path = os.path.join(folder_path, file_name)
            
            # Try reading the CSV file into a DataFrame using the correct delimiter
            try:
                pd.read_csv(file_path, delimiter=';')
            except Exception as e:
                # Add the problematic file to the list
                error_files.append({
                    'folder': folder,
                    'file_name': file_name,
                    'error': str(e)
                })

# Re-initialize the empty DataFrame to hold the merged data
merged_df = pd.DataFrame()

# Loop through each folder and read the CSV files
for folder in unzipped_contents:
    # Skip the __MACOSX folder
    if folder == '__MACOSX':
        continue
    
    folder_path = os.path.join(unzip_dir_path, folder)
    
    # Loop through each file in the folder
    for file_name in os.listdir(folder_path):
        # Skip system files like .DS_Store and the problematic files identified earlier
        if file_name.endswith('.csv') and {'folder': folder, 'file_name': file_name} not in error_files:
            file_path = os.path.join(folder_path, file_name)
            
            # Try reading the CSV file into a DataFrame using the correct delimiter
            try:
                temp_df = pd.read_csv(file_path, delimiter=';')
                
                # Add a new column with the folder name (canton)
                temp_df['canton'] = folder
                
                # Append the DataFrame to the merged DataFrame
                merged_df = pd.concat([merged_df, temp_df], ignore_index=True)
                
            except Exception as e:
                # Log any new errors for future reference (though we expect none at this stage)
                error_files.append({
                    'folder': folder,
                    'file_name': file_name,
                    'error': str(e)
                })

# Loop through the problematic files and read them into DataFrames after skipping the last column
for error_file in error_files:
    folder = error_file['folder']
    file_name = error_file['file_name']
    file_path = os.path.join(unzip_dir_path, folder, file_name)
    
    try:
        # Read the CSV file but skip the last column
        temp_df = pd.read_csv(file_path, delimiter=';', usecols=lambda x: x not in [temp_df.columns[-1] for temp_df in [pd.read_csv(file_path, delimiter=';', nrows=1)]])
        
        # Add a new column with the folder name (canton)
        temp_df['canton'] = folder
        
        # Append the DataFrame to the merged DataFrame
        merged_df = pd.concat([merged_df, temp_df], ignore_index=True, sort=False)
        
    except Exception as e:
        # Log any new errors for future reference (though we expect none at this stage)
        error_files.append({
            'folder': folder,
            'file_name': file_name,
            'error': str(e)
        })

# Save the final merged DataFrame to a CSV file
merged_csv_path = 'merged_data.csv'
merged_df.to_csv(merged_csv_path, index=False)

# Step 1: Filter the DataFrame based on the conditions
filtered_df = merged_df[(merged_df['page_is_software_guide'] != 'No') | (merged_df['page_contains_software_guide'] != 'No')]

# Step 2: Initialize the "page_topic" column with a default value
filtered_df['page_topic'] = 'Others'

# Define a list of keywords associated with each topic for classification
topic_keywords = {
    'Finance and taxes': ['tax', 'finance', 'financial', 'budget', 'revenue'],
    'E-governance and administration': ['e-governance', 'administration', 'government', 'public service'],
    'Social and public security': ['social security', 'public security', 'welfare', 'safety'],
    'Health': ['health', 'medical', 'hospital', 'healthcare'],
    'Education': ['education', 'school', 'university', 'learning'],
    'Communication and collaboration': ['communication', 'collaboration', 'network', 'internet'],
    'Legal services and conformity': ['legal', 'law', 'compliance', 'regulation'],
    'Statistics and data analysis': ['statistics', 'data', 'analysis', 'analytics'],
    'Culture and tourism': ['culture', 'tourism', 'museum', 'travel'],
    'Environment, agriculture and natural resources': ['environment', 'agriculture', 'natural resources', 'climate'],
    'Maps, infrastructures and territorial planning': ['map', 'infrastructure', 'territory', 'planning'],
    'Archives and document management': ['archive', 'document', 'file', 'management'],
    'Human resources': ['human resources', 'HR', 'employment', 'staff'],
    'Purchasing and procurement': ['purchase', 'procurement', 'supply', 'vendor']
}

# Perform keyword-based classification for each row
for topic, keywords in topic_keywords.items():
    for keyword in keywords:
        filtered_df.loc[filtered_df['page_content'].str.contains(keyword, case=False, na=False), 'page_topic'] = topic

# Show the first few rows of the filtered and classified DataFrame
filtered_df.head()

# Save the filtered and classified DataFrame to a new CSV file
filtered_csv_path = 'filtered_classified_data.csv'
filtered_df.to_csv(filtered_csv_path, index=False)

