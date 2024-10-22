# EU ODA Targets Analysis Repository

This repository provides the data and code used for the analysis of EU Official Development Assistance (ODA) targets, focusing on the required spending by EU countries and institutions to meet their ODA commitments by 2030. The analysis also includes projections for EU Institutions' spending during the 2027-2034 period.

### Methodology Overview

Full information on the methodology and sources can be [found here.](https://one-campaign.observablehq.cloud/eu-oda/)

Our analysis estimates how much EU countries and institutions need to spend to achieve their ODA targets. The key elements include:

- **ODA/GNI Ratios**: Calculation of the ratio of ODA to Gross National Income (GNI) for each EU member state, based on the latest available data from the OECD Development Assistance Committee (DAC).
- **GNI Growth Projections**: Use of the IMF World Economic Outlook (WEO) to project GNI growth, using constant GDP growth rates as a proxy to develop future GNI figures, and determine the future spending required for each country to meet their ODA targets.
- **Historical EU Institutions ODA**: Analysis of historical contributions from EU Institutions, differentiating between imputable and non-imputable portions of ODA, to estimate future requirements.

### Data Sources

- **ODA and GNI Data**: OECD Development Assistance Committee datasets, including ODA reported as grant equivalents.
- **Economic Projections**: IMF World Economic Outlook (WEO) projections for GDP, used as a proxy for GNI growth.


### Repository Contents

- **Scripts**: Python scripts for loading, processing, and analyzing the data.
    - `ms_analysis.py` and `eu_institutions.py` contain the core analysis for Member States and EU Institutions respectively.
    - `tools.py` and `common.py` provide utility functions and constants used throughout the analysis.
- **Data**: Folder paths and handling defined in `config.py` to ensure consistent reference to data and output locations.
