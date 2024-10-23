---
title: EU ODA targets
toc: true
sidebar: false
---


```js
const  targetData = await FileAttachment("./data/targets.json").json()
const targetTableData = Object.entries(targetData).map(([country, target]) => ({country, target}))
```

```js display
const targetTable = Inputs.table(targetTableData,
{sort: "country", reverse: false, select:false, rows:10.1, format: {target: d3.format(".2%")}})
```


# EU Official Development Assistance (ODA) targets

This page presents our methodology to estimate the required ODA spending for EU countries to meet their ODA targets by 2030. It also outlines how we use historical data to estimate the required spending for the EU Institutions for the 2027-2034 period.

<div class="note">
For this work, we use ODA and GNI data from the OECD Development Assistance Committee. We also use economic projections from the IMF World Economic Outlook. We present ODA data following OECD DAC conventions and definitions. Data from 2018 is presented as grant equivalents. Unless otherwise noted, all amounts are in 2025 constant prices.
</div>

---

## Where are we today?
The latest year with available ODA data is 2023. These numbers are preliminary and subject to change. This data includes GNI estimates for all donors.

Since 2022, there has been a significant increase in in-donor refugee costs and aid to Ukraine. Since 2020, donors have also spent a significant amount of ODA on COVID-19 response. We do not yet have a full picture of how much ODA was spent on these items in 2023.

In 2023, the EU collectively spent **0.57%** of its GNI, or **€96.5 billion**, on ODA.  
<br>

## What are the targets?

While EU countries have committed to spending 0.7% of their collective GNI on ODA, individual countries have different targets. Some have committed to spending 0.70% of their GNI by 2030, while others have committed to spending 0.33% as ODA.

<br>

<div style="max-width:440px; margin-left:5%">
<h3>Individual country targets</h3>
${targetTable}
</div>

<br>
<br>


## Estimating the required spending to meet the targets

In order to estimate how much countries will need to spend by 2030 in order to meet their targets, we need two basic ingredients:
1. Data on how much they are spending now, a share of GNI.
2. Projections for how much their GNI will grow in the future.

#### ODA/GNI data
For the first, we use the latest available data, for 2023, as reported to the OECD DAC. This data measures Official Development Assistance (in grant equivalent terms) as a share of Gross National Income (GNI) for each EU country.

#### GNI growth projections
For the second, we use the October 2024 IMF World Economic Outlook (WEO) projections for GDP growth. We use these projections as a proxy for GNI growth. We apply these projections to the latest GNI numbers to estimate how much countries will need to spend in the future to meet their targets.

The WEO projections are available up to 2028. For years beyond 2028, we use the average growth rate for 2026-28, and assume it will hold constant until 2034.

#### Projecting the required spending
We assume that countries will meet their ODA targets by 2030, and that they will get to their targets with linear yearly increases. For countries who are already spending above their target, we assume that they will sustain their current level of ODA spending as a percentage of GNI.

The following table shows how much EU 27 countries would have to spend per year to meet their **individual** targets by 2030, and sustain that spending (as a share of GNI) until 2034. 


```js
const additionalSpendingData = FileAttachment("./data/additional_spending_yearly.csv").csv({typed:true})
```

```js
const country = view(Inputs.select(["All"].concat(additionalSpendingData.map(d=>d.name_short)), {value: "All", label: "Select a country", unique: true, sort:true}));
```


<div class="card" style="max-width: 720px; padding: 0;">

```js
const additionalSpendingTable = view(Inputs.table(additionalSpendingData.filter(d => d.indicator == "Full" && d.name_short == country || country=="All"),{
    rows: 13.2,
    columns: ["year","name_short", "oda_gni_ratio", "oda", "additional_oda"],
    header: {"year": "Year", "oda_gni_ratio": "ODA/GNI (%)", "oda": "Projected ODA", "additional_oda": "Additional ODA",
        "name_short": "Country",
    },
    width: {
        "year": 100,
        "name_short": 130
     },
     layout: "auto",

     format:{
        year: d=>d.toFixed(0),
        oda_gni_ratio: d => (100*d).toFixed(2),
        oda: d=> d.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 1})+"m",
        additional_oda: d=> d.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 1})+"m",
     },
     align:{
        year: "left"
     }

}))
```

</div>

Putting it all together, for the 2028 to 2034 period, EU countries would need to spend **€984 billion** euros to meet their ODA targets (in 2025 constant prices).

The following chart shows actual and required ODA spending for EU Member States, from 2018 to 2034.

<div class="card" style="max-width: 720px; padding: 0;">
<iframe src='https://flo.uri.sh/visualisation/19898927/embed' title='Interactive or visual content' class='flourish-embed-iframe' frameborder='0' scrolling='no' style='width:100%;height:600px;' sandbox='allow-same-origin allow-forms allow-scripts allow-downloads allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation'></iframe>
</div>


---

## The role of the EU Institutions

For this analysis we distinguish two key components of the ODA provided by the EU institutions: ODA imputable to EU member states, and ODA which is not imputable to EU member states.

The imputable portion refers to ODA that is counted towards the ODA targets of EU member states. These amounts are reported by member states to the OECD DAC, as part of the *Members use of the Multilateral System* dataset. The non-imputable portion refers to the difference between what the EU Institutions spend in a given year, and the amount that is imputable to EU member states.

The following chart shows the breakdown of EU spending from 2014 to 2022, as percentages of *Total EU ODA*.

Headline ODA (e.g what counts against the 0.7 target) is the sum what what this chart shows as "Member States" and "Imputable EU Institutions ODA".

*Total EU ODA* provided by the EU Member States and the EU Institutions, additionally includes the non-imputable portion.

<div class="card" style="max-width: 720px; padding: 0;">
<iframe src='https://flo.uri.sh/visualisation/19902177/embed' title='Interactive or visual content' class='flourish-embed-iframe' frameborder='0' scrolling='no' style='width:100%;height:600px;' sandbox='allow-same-origin allow-forms allow-scripts allow-downloads allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation'></iframe>
</div>

#### Projecting the required spending

As noted above, for the 2028 to 2034 period, EU countries would need to spend **€984 billion** euros to meet their ODA targets (in 2025 constant prices).

To arrive at a number for the EU Institutions, we look at the historical breakdown of EU ODA in order to determine how much of EU Member states' ODA has been provided by the EU Institutions, both as imputable and non-imputable ODA.

For the period 2014-2020, we look at Total EU ODA as EU28 ODA + EU Institutions ODA (imputable and non-imputable). For the period 2021-2022 (the latest year with complete data), we look at Total EU ODA as EU27 ODA + EU Institutions ODA (imputable and non-imputable).

In 2025 prices, between 2014 and 2020:
- EU Member States spent €805 billion
- The EU Institutions spent €195.7 billion
  - *Of which*, €178.8 billion was imputable to EU Member States and €16.9. billion was non-imputable

That means that the EU Institutions provided provided 22.2% of the total ODA spent by EU Member States (e.g. the imputable portion of EU Institutions ODA). This imputable portion represented 91.3% of the total ODA provided by the EU Institutions.

Putting it all together, based on our estimate of required EU Member States spending (i.e €984 billion for 2028-2034), if the historical shares outlined above remained constant, the EU Institutions would need to spend **€239.2 billion** over that period (€218.5 billion of which would be imputable to EU Member States and €20.7 billion would be non-imputable).


---

## Data and replication code
All data and code used in this analysis is available through this [GitHub repository](https://github.com/ONEcampaign/eu_mff).