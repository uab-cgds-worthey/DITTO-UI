import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import yaml
import requests
import json

# Config the whole app
st.set_page_config(
    page_title="DITTO",
    page_icon="🧊",
    layout="wide",  # initial_sidebar_state="expanded",
)


@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8")


@st.cache
def get_config():
    with open("./configs/col_config.yaml") as fh:
        config_dict = yaml.safe_load(fh)
    return config_dict


# @st.cache(allow_output_mutation=True)
def load_gene_data(gene_name):
    pkd = pd.read_csv(f"./data/slim_dbnsfp_predictions/{gene_name}_ditto_predictions.csv.gz")
    # pkd = pkd[pkd["aapos"] != -1].reset_index(drop=True)
    # pkd.sort_values(by=["aapos", "Ditto_Deleterious"], ascending=[True, False])
    # pkd["clinvar_clnsig"] = pkd["clinvar_clnsig"].replace(".", "not seen in clinvar")
    pkd = pkd.replace(np.nan, "N/A")
    pkd = pkd.replace(".", "N/A")
    class_color = {
        "Pathogenic": "#b2182b",
        "Pathogenic/Likely_pathogenic": "#b2182b",
        "Likely_pathogenic": "#d73027",
        "Uncertain_significance": "#5ab4ac",
        "Uncertain_significance,_other": "#5ab4ac",
        "Likely_benign": "#2166ac",
        "Benign/Likely_benign": "#2166ac",
        "Benign": "#3182bd",
        "not seen in clinvar": "#5ab4ac",
        "other": "#5ab4ac",
        "not_provided": "#5ab4ac",
        "Conflicting_interpretations_of_pathogenicity": "#d8b365",
    }
    return pkd, class_color


def get_domain(gene_name):
    response = requests.get(
        f"https://rest.uniprot.org/uniprotkb/search?&query=gene_exact:{gene_name} AND (taxonomy_id:9606) AND (reviewed:true)"
    )
    info_dict = response.json()
    fullname = info_dict["results"][0]["proteinDescription"]["recommendedName"]["fullName"]["value"]
    uniprotid = info_dict["results"][0]["primaryAccession"]
    try:
        domain = pd.DataFrame(info_dict["results"][0]["features"])
        domain = domain[domain["type"] == "Domain"][["type", "location", "description"]]
        domain[["start", "end"]] = domain["location"].apply(pd.Series)
        domain[["start", "modifier"]] = domain["start"].apply(pd.Series)
        domain[["end", "modifier"]] = domain["end"].apply(pd.Series)
        domain = domain.drop(["location", "modifier"], axis=1)
        domain = domain.reset_index(drop=True)
    except:
        # initialise data of lists.
        domain = {"type": ["Domain"], "description": ["null"], "start": [0], "end": [0]}

        # Create DataFrame
        domain = pd.DataFrame(domain)
    del info_dict, response
    return fullname, uniprotid, domain


def domain_count(data, domain):

    for clinvar_class in list(data["clinvar_clnsig"].unique()):
        # Use .iterrows() to iterate over Pandas rows
        for idx, row in domain.iterrows():
            domain.loc[idx, clinvar_class] = len(
                data[
                    (data["aapos"] >= row["start"])
                    & (data["aapos"] <= row["end"])
                    & (data["clinvar_clnsig"] == clinvar_class)
                ]
            )
    return domain


def pkd_plot(st, data, class_color):
    st.write(f"Total variant-transcript pairs = {len(data)}")
    # st.write(f"Total domains = {len(domain)}")
    st.markdown("**Interactive scatter plot with nsSNVs**")

    pkd1 = px.scatter(
        data,
        x="pos(1-based)",
        y="Ditto_Deleterious",
        labels={
            "pos(1-based)": "position",
            "Ditto_Deleterious": "Ditto Deleterious Score",
            # "clinvar_clnsig": "Clinvar Classification",
        },
    )

    pkd1.add_hline(y=0.91, line_width=2, line_dash="dash", line_color="red")

    # for idx, row in domain.iterrows():
    #    pkd1.add_vrect(
    #        x0=row["start"],
    #        x1=row["end"],
    #        line_width=0,
    #        opacity=0.3,
    #        fillcolor="LightSalmon",
    #        annotation_text=row["description"],  # row["short_domain"],
    #        annotation_position="outside top",
    #        annotation_textangle=45,
    #        # annotation=dict(font_size=10, font_family="Times New Roman"),
    #    )
    st.plotly_chart(pkd1, use_container_width=True)

    return None


def main():

    st.subheader("Gene view of non-synonymous variants from dbNSFP")
    st.write("**Methods:**")
    st.markdown(
        "- Non-Synonymous Single Nucleotide Variants (nsSNVs) are downloaded from [dbNSFP](http://database.liulab.science/dbNSFP) and run through DITTO (unpublished) for deleterious predictions."
    )
    st.markdown(
        "- Each dot in the below interactive scatter plots is a variant-transcript pair i.e. variant positioned on one of the Ensemble transcripts. Colors of each dot represents the [Clinvar](https://www.ncbi.nlm.nih.gov/clinvar/) Classification denoted by the same color in figure legends. "
    )
    st.markdown(
        "- The red dashed line represents the cutoff of DITTO score (0.91) to be classified as highly deleterious to the protein."
    )
    # st.markdown(
    #    "- Domains of PKD1/2 are mapped according to their Amino Acid positions and are represented on top of the plot with different colors. The bar plot below shows the number of variants classified in to each clinvar class per each domain."
    # )
    st.markdown(
        "- Scatterplot is made with [Python Plotly](https://plotly.com/python/) and is interactive, can be viewed in full screen."
    )
    st.markdown("- Please select/unselect clinvar classes for better interactive visualization")
    st.markdown("--------")

    config_dict = get_config()

    gene_name = st.sidebar.selectbox(
        "Select Gene Name:",
        options=[""] + list(config_dict["genes"]),
    )

    if gene_name == "":
        st.markdown("Please select a Gene from the dropdown above!")
    else:
        pkd_vars, class_color = load_gene_data(gene_name)

        st.sidebar.download_button(
            label=f"Download {gene_name} variants",
            data=convert_df(pkd_vars),
            file_name=f"{gene_name}_DITTO_predictions.csv",
            mime="text/csv",
        )
        #
        # fullname, uniprotid, domain = get_domain(gene_name)
        # st.subheader(f"{gene_name} ({fullname}) non-synonymous variants from dbNSFP")
        # domain = domain_count(pkd_vars, domain)
        # st.dataframe(domain)
        # st.sidebar.download_button(
        #    label=f"Download {gene_name} domains",
        #    data=convert_df(domain),
        #    file_name=f"{gene_name}_domains.csv",
        #    mime="text/csv",
        # )

        pkd_plot(st, pkd_vars, class_color)

    st.markdown("---")
    left_info_col, right_info_col = st.columns(2)
    left_info_col.markdown(
        f"""
        ### Authors
        Please feel free to contact us with any issues, comments, or questions.
        ##### Tarun Mamidi [![Twitter URL](https://img.shields.io/twitter/url/https/twitter.com/bukotsunikki.svg?style=social&label=Follow%20%40TarunMamidi7)](https://twitter.com/TarunMamidi7)
        - Email:  <tmamidi@uab.edu> or <mtkk94@gmail.com>
        - GitHub: https://github.com/tkmamidi
        ##### Dr. Liz Worthey [![Twitter URL](https://img.shields.io/twitter/url/https/twitter.com/bukotsunikki.svg?style=social&label=Follow%20%40lizworthey)](https://twitter.com/lizworthey)
        - Email: <lworthey@uab.edu>
        - GitHub: https://github.com/uab-cgds-worthey
        """,
    )
    right_info_col.markdown(
        """
        ### Funding
        - NIH
        - CGDS Lab Funds
         """
    )
    right_info_col.markdown(
        """
        ### License
        TBD
        """
    )
    st.markdown("---")
    st.markdown("Developed and Maintained by [Tarun Mamidi](https://www.linkedin.com/in/tkmamidi/)")
    st.markdown("[Center for Computational Genomics and Data Science](https://sites.uab.edu/cgds/)")
    # st.markdown(f"Most Recently Deposited Entry 09/28/2022")
    st.markdown("Copyright (c) 2022 CGDS")


if __name__ == "__main__":
    main()
