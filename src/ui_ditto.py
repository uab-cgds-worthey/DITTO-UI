import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import yaml
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ClinSigColors:
    default_colors = {
        "not seen in clinvar": "#969696",
        "other": "#969696",
        "not provided": "#969696",
        "Conflicting interpretations of pathogenicity": "#d8b365",
        "Benign": "#3182bd",
        "Likely benign": "#2166ac",
        "Benign/Likely benign": "#2166ac",
        "Uncertain significance": "#5ab4ac",
        "Uncertain significance, other": "#5ab4ac",
        "Pathogenic/Likely pathogenic": "#b2182b",
        "Likely pathogenic": "#d73027",
        "Pathogenic": "#b2182b",
    }


# Config the whole app
st.set_page_config(
    page_title="DITTO",
    page_icon="🧊",
    layout="wide",  # initial_sidebar_state="expanded",
)


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8")


@st.cache_data
def get_config():
    with open("./configs/col_config.yaml") as fh:
        config_dict = yaml.safe_load(fh)
    return config_dict


@st.cache_data(
    max_entries=50
)  # limit number of genes loaded in cache to 50 to prevent reaching memory limits
def load_gene_data(gene_name):
    ditto_gene_preds_df = pd.read_csv(
        f"./data/dbnsfp_predictions/slim_dbnsfp_predictions/{gene_name}_ditto_predictions.csv.gz"
    )
    ditto_gene_preds_df = ditto_gene_preds_df[ditto_gene_preds_df["aapos"] != -1].reset_index(
        drop=True
    )
    ditto_gene_preds_df.sort_values(by=["aapos", "Ditto_Deleterious"], ascending=[True, False])
    ditto_gene_preds_df["clinvar_clnsig"] = ditto_gene_preds_df["clinvar_clnsig"].replace(
        ".", "not seen in clinvar"
    )
    ditto_gene_preds_df = ditto_gene_preds_df.replace(np.nan, "N/A")
    ditto_gene_preds_df = ditto_gene_preds_df.replace(".", "N/A")
    return ditto_gene_preds_df


def query_external_api(api_url):
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    response = http.get(api_url, headers=headers)

    # raise exception if 4XX or 5XX status code returned from server after 3 retries
    resp_dict = None
    try:
        response.raise_for_status()
        resp_dict = response.json()
    except requests.exceptions.RequestException as expt:
        print(
            f"Failed to query {api_url}, code: {response.status_code}, reason: {response.reason},"
            f" text: {response.text}, error: {str(expt)}"
        )
    finally:
        http.close()  # this will release resources so that the GC can clean up the request and response objects

    return resp_dict


@st.cache_data(
    ttl=3600
)  # expire cached results of the Uniprot query after 1 hour for the requested gene
def get_domain(gene_name):
    uniprot_url = f"https://rest.uniprot.org/uniprotkb/search?query=gene_exact:{gene_name}+AND+organism_id:9606&format=json&fields=ft_domain,cc_domain,protein_name"
    info_dict = query_external_api(uniprot_url)

    # set defaults for uniprot return information
    fullname = ""
    domain = []

    if len(info_dict["results"]) > 0:
        first_rec = info_dict["results"][0]
        if "recommendedName" in first_rec.get("proteinDescription"):
            fullname = (
                first_rec.get("proteinDescription")
                .get("recommendedName")
                .get("fullName")
                .get("value")
            )
        elif "submissionNames" in first_rec.get("proteinDescription"):
            fullname = (
                first_rec.get("proteinDescription")
                .get("submissionNames")[0]
                .get("fullName")
                .get("value")
            )

        for feature in info_dict["results"][0]["features"]:
            if feature["type"] == "Domain":
                domain.append(
                    {
                        "type": "Domain",
                        "description": feature["description"],
                        "start": int(feature["location"]["start"]["value"]),
                        "end": int(feature["location"]["end"]["value"]),
                    }
                )

    if len(domain) == 0:
        domain.append({"type": "Domain", "description": "", "start": 0, "end": 0})

    del info_dict
    return fullname, pd.DataFrame(domain)


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


def gene_plot(st, data, class_color, domain):
    st.write(f"Total variant-transcript pairs = {len(data)}")
    st.write(f"Total domains = {len(domain)}")
    st.markdown("**Interactive scatter plot with nsSNVs**")

    class_list = [
        tuple for x in class_color.keys() for tuple in data.clinvar_clnsig.unique() if tuple == x
    ]

    data.clinvar_clnsig = data.clinvar_clnsig.astype("category")
    data.clinvar_clnsig = data.clinvar_clnsig.cat.set_categories(class_list)
    data = data.sort_values(["clinvar_clnsig"])

    gene_scatter_plot = px.scatter(
        data,
        x="aapos",
        y="Ditto_Deleterious",
        color="clinvar_clnsig",
        # opacity=0.3,
        hover_data=[
            "aapos",
            "HGVSc_VEP",
            "Ensembl_transcriptid",
            "HGVSp_VEP",
            "CADD_phred",
            "gnomAD_genomes_AF",
            "clinvar_review",
        ],
        hover_name="HGVSp_VEP",
        labels={
            "aapos": "AA position",
            "Ditto_Deleterious": "Ditto Deleterious Score",
            "clinvar_clnsig": "Clinvar Classification",
        },
        color_discrete_map=class_color,
    )

    gene_scatter_plot.add_hline(y=0.91, line_width=2, line_dash="dash", line_color="red")
    gene_scatter_plot.update_layout(legend_traceorder="reversed")

    for _, row in domain.iterrows():
        gene_scatter_plot.add_vrect(
            x0=row["start"],
            x1=row["end"],
            line_width=0,
            opacity=0.3,
            fillcolor="LightSalmon",
            annotation_text=row["description"],  # row["short_domain"],
            annotation_position="outside top",
            annotation_textangle=45,
            # annotation=dict(font_size=10, font_family="Times New Roman"),
        )
    st.plotly_chart(gene_scatter_plot, use_container_width=True)
    st.markdown("**Clinvar classifications by domain**")
    st.dataframe(domain)
    if np.nan in list(data["clinvar_clnsig"].unique()):
        classes = list(data["clinvar_clnsig"].unique())
        classes = [item for item in classes if str(item) != "nan"]
    else:
        classes = list(data["clinvar_clnsig"].unique())

    stack_bar = px.bar(
        domain,
        x="description",
        y=classes,
        hover_name="description",
        # hover_data=["Gene symbol"],
        labels={
            "description": "Domain",
            "clinvar_clnsig": "Clinvar Classification",
            "value": "# of variants",
            "variable": "Clinvar Classification",
        },
        # title="Clinvar classifications by domain",
        color_discrete_map=class_color,
    )

    st.plotly_chart(stack_bar, use_container_width=True)

    return None


def main():
    st.subheader("Gene view of non-synonymous variants from dbNSFP")
    st.write("**Methods:**")
    st.markdown(
        "- Non-Synonymous Single Nucleotide Variants (nsSNVs) are downloaded from"
        " [dbNSFP](http://database.liulab.science/dbNSFP) and run through DITTO (unpublished) for"
        " deleterious predictions."
    )
    st.markdown(
        "- Each dot in the below interactive scatter plots is a variant-transcript pair i.e."
        " variant positioned on one of the Ensemble transcripts. Colors of each dot represents the"
        " [Clinvar](https://www.ncbi.nlm.nih.gov/clinvar/) Classification denoted by the same color"
        " in figure legends. "
    )
    st.markdown(
        "- The red dashed line represents the cutoff of DITTO score (0.91) to be classified as"
        " highly deleterious to the protein."
    )
    st.markdown(
        "- Scatterplot is made with [Python Plotly](https://plotly.com/python/) and is interactive,"
        " can be viewed in full screen."
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
        gene_vars = load_gene_data(gene_name)
        gene_vars["genename"] = gene_name

        with open(
            f"./data/dbnsfp_predictions/slim_dbnsfp_predictions/{gene_name}_ditto_predictions.csv.gz",
            "rb",
        ) as dl_gene_file:
            st.sidebar.download_button(
                label=f"Download {gene_name} variants",
                data=dl_gene_file,
                file_name=f"{gene_name}_DITTO_predictions.csv",
                mime="application/octet-stream",
            )

        fullname, domain = get_domain(gene_name)
        st.subheader(f"{gene_name} ({fullname}) non-synonymous variants from dbNSFP")
        domain = domain_count(gene_vars, domain)
        # st.dataframe(domain)
        st.sidebar.download_button(
            label=f"Download {gene_name} domains",
            data=convert_df(domain),
            file_name=f"{gene_name}_domains.csv",
            mime="text/csv",
        )

        gene_plot(st, gene_vars, ClinSigColors.default_colors, domain)

    st.markdown("---")
    left_info_col, right_info_col = st.columns(2)
    left_info_col.markdown(
        """
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
        GNU General Public License\n
        Version 3, 29 June 2007
        """
    )
    st.markdown("---")
    st.markdown("Developed and Maintained by [Tarun Mamidi](https://www.linkedin.com/in/tkmamidi/)")
    st.markdown("[Center for Computational Genomics and Data Science](https://sites.uab.edu/cgds/)")
    # st.markdown(f"Most Recently Deposited Entry 09/28/2022")
    st.markdown("Copyright (c) 2022 CGDS")


if __name__ == "__main__":
    main()
