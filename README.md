# Beyond the Lab: An In-Depth Analysis of Real-World Practices in Government-to-Citizen Software User Documentation

Welcome to the replication package of the paper "Beyond the Lab: An In-Depth Analysis of Real-World Practices in Government-to-Citizen Software User Documentation". This repository contains a suite of tools and scripts used in the research project aimed at analyzing government-to-citizen software user documentation, particularly focusing on the Swiss Digital Strategy program. The project extends existing literature by conducting a large-scale, real-world analysis of user guides. Nearly 600 user guides were scrutinized, identified from about 5,000 links on the websites of 18 German-speaking Swiss cantons. This analysis correlates the presence of key guide features with socio-economic factors of the cantons.

## Abstract

Compliance with the EU's Platform-to-Business (P2B) Regulation is challenging for online platforms, and the assessment of their compliance is difficult for public authorities. This is partly due to the lack of automated tools for assessing the information platforms provide in their terms and conditions (i.e., software documentation), in relation to ranking transparency. That gap also creates uncertainty regarding the usefulness of such documentation for end-users. Our study tackles this issue in two ways. First, we empirically evaluate the compliance of six major platforms, revealing substantial differences in their documentation. Second, we introduce and test automated compliance assessment tools based on ChatGPT and information retrieval technology. These tools are evaluated against human judgments, showing promising results as reliable proxies for compliance assessments. Our findings could help enhance regulatory compliance and align with the United Nations Sustainable Development Goal 10.3, which seeks to reduce inequality, including business disparities on these platforms.

## Contents

- `0_link_scraping`: Contains scripts for scraping links from official websites.
- `1_guide_identification`: Stores processed results from ChatGPT and their manual corrections, related to guide identification.
- `2_web_classification`: Includes scripts for classifying web content.
  - `statistical_analysis.py`: Analyzes classification results of web content.
  - `content_classifier.py`: Classifies web content based on predefined criteria.
- `3_pdf_classification`: Scripts for classifying PDF content.
  - `statistical_analysis.py`: Performs statistical analysis of the classified PDF content.
  - `content_classifier.py`: Classifies the content of PDF documents.
- `4_web+pdf_classification`: Combined analysis of web and PDF content.
  - `statistical_analysis.py`: Merges and analyzes data from both web and PDF content.
- `5_correlation_analysis`: Correlation analysis scripts.
  - `analysis_script_guides.py`: Analyzes correlations within user guides.
  - `analysis_script_scraped_links.py`: Analyzes correlations within scraped links.
- `requirements.txt`: List of Python packages required to run the scripts.

## Installation

1. Ensure Python 3.x is installed on your system.
2. Clone this repository to your local machine.
3. Navigate to the cloned directory and install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Follow the directory numbering when executing scripts, beginning with link scraping and proceeding through guide identification, classification, and correlation analysis.

### Running Scripts

1. **Link Scraping**:
   - Navigate to `0_link_scraping`.
   - Run `link_data_generator.py` to collect links. Results are stored in the same directory.

2. **Guide Identification**:
   - Review the content in `1_guide_identification`, containing outputs from ChatGPT and manual corrections.

3. **Web and PDF Classification**:
   - For web content classification:
     - Navigate to `2_web_classification`.
     - Run `content_classifier.py` first, followed by `statistical_analysis.py`. The latter script generates visualizations, with results saved in the same directory.
   - For PDF content classification:
     - Navigate to `3_pdf_classification`.
     - Run `content_classifier.py` first, followed by `statistical_analysis.py`. Results, including visualizations, are stored in the same directory.

4. **Combined Web and PDF Analysis**:
   - Navigate to `4_web+pdf_classification`.
   - Run `statistical_analysis.py` for a comprehensive analysis. Results are saved in the same directory.

5. **Correlation Analysis**:
   - Navigate to `5_correlation_analysis`.
   - Run `analysis_script_guides.py` and `analysis_script_scraped_links.py`. Both scripts produce visualizations and store results in the same directory as PDF files.

### Results

Results are saved within the same directories as the scripts. Look for output files in formats such as PDF, CSV, JSON, or specific directories mentioned in the scripts' documentation.

## Contributing

Contributions to this project are welcome. Please submit pull requests or issues through the repository's issue tracker.

## Conclusion

This replication package provides a comprehensive framework for analyzing government-to-citizen software user documentation practices. It is designed to be flexible, allowing researchers to replicate the study and build upon its findings.

## Support

For any problem or question, please contact me at `cesco.sovrano@gmail.com`