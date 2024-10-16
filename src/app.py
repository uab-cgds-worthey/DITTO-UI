import streamlit as st
import pandas as pd
from subprocess import Popen, PIPE

# Config the whole app
st.set_page_config(
    page_title="DITTO",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "clicked" not in st.session_state:
    st.session_state.clicked = False


def click_button():
    st.session_state.clicked = True

# @st.cache_data
def tabix_query(chrom , start):
    """Call tabix and generate an array of strings for each line it returns."""
    chrom = 'chr'+str(chrom)
    query = '{}:{}-{}'.format(chrom, start, start)
    # st.warning(f"Querying DITTO for {query}")
    try:
        process = Popen(['tabix', '-f', f'https://s3.lts.rc.uab.edu/cgds-public/dittodb/DITTO_{chrom}.tsv.gz', query], stdout=PIPE)
        for line in process.stdout:
            yield line.strip().decode("utf-8").split('\t')
    except Exception as e:
        st.warning(e)
        st.warning(f"Could not query using BCFtools!")
        st.session_state.clicked = False

def main():

    head_col1, head_col2 = st.columns([2, 1])
    head_col1.markdown("# DITTO")
    head_col1.markdown(
        "### A tool for exploring small genetic variants and their predicted functional impact."
    )
    head_col1.markdown(
        "- DITTO (inspired by pokemon) is a tool for exploring any type of small genetic variant and their predicted functional impact on transcript(s)."
    )
    head_col1.markdown(
        "- DITTO utilizes annotations from [OpenCravat](https://run.opencravat.org/), a tool for annotating variants with information from multiple data sources."
    )
    head_col1.markdown(
        "- DITTO is currently trained on GRCh38 variants from [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/) and is not intended for clinical use."
    )

    head_col2.markdown(
        "![GIF Placeholder](https://media.giphy.com/media/pMFmBkBTsDMOY/giphy.gif)"
    )

    head_col1.markdown("\n\n")

    st.markdown("### Please input a variant of interest in build GRCh38:")
    st.markdown(
        "**Note:** Please use the correct variant info for the build. You can check the correct variant info at [Ensembl](https://www.ensembl.org/index.html) or [UCSC](https://genome.ucsc.edu/index.html)."
    )
    st.warning(f"Examples: \n\nSNV - 2, 32250098\n\nDEL - 16, 56870739\n\nINS - 16, 56870707\n\nINS - 1, 4956111")

    # Variant input
    col1, col2 = st.columns(2)
    chrom = col1.selectbox("Chromosome:", options=list(range(1, 23)) + ["X", "Y", "M"])
    pos = col2.text_input("Position:", 2406483)
    st.dataframe(
        pd.DataFrame(
            {
                "num_legs": [2, 4, 8, 0],
                "num_wings": [2, 0, 0, 0],
                "num_specimen_seen": [10, 2, 1, 8],
            },
            index=["falcon", "dog", "spider", "fish"],
        )
    )
    process = Popen(
        [
            "echo",
            "Mana is great!!"
        ],
        stdout=PIPE,
    )
    st.write(process.stdout.read().decode("utf-8"))

    # Submit button to query variant annotations and predict functional impact
    st.button("Submit", on_click=click_button)
    if st.session_state.clicked:

        try:
            vars = list(tabix_query(chrom,pos))
        except:
            vars = []
            st.session_state.clicked = False

        # Check if variant annotations are found
        if not vars:
            st.warning(
                "Could not extract variants at this position. Please check or try a different position!", icon="⚠️"
            )
            st.session_state.clicked = False

        else:
            # Display variant annotations from opencravat
            st.subheader("**Variants with DITTO predictions**")
            overall = pd.DataFrame(vars, columns = ['Chromosome', 'Position','Reference Allele','Alternate Allele','Transcript','Gene','Consequence','DITTO'])
            st.warning(f"Showing {len(overall)} variants")
            st.dataframe(overall,hide_index=True, use_container_width=True)
            st.write("\n\n")

    st.markdown("---")

    left_info_col, right_info_col = st.columns(2)
    left_info_col.markdown(
        f"""
        ### Authors
        DITTO is a work in progress and we welcome your feedback and suggestions on our [GitHub page](https://github.com/uab-cgds-worthey/DITTO-UI).""",
    )
    left_info_col.markdown("\n\n")
    left_info_col.markdown(
        f"""
        ##### Tarun Mamidi [![Twitter URL](https://img.shields.io/twitter/url/https/twitter.com/bukotsunikki.svg?style=social&label=Follow%20%40TarunMamidi7)](https://twitter.com/TarunMamidi7)
        - Email:  <tmamidi@uab.edu> or <mtkk94@gmail.com>
        - GitHub: https://github.com/tkmamidi
        """
    )
    left_info_col.markdown("\n\n")
    left_info_col.markdown(
        f"""
        ##### Dr. Liz Worthey [![Twitter URL](https://img.shields.io/twitter/url/https/twitter.com/bukotsunikki.svg?style=social&label=Follow%20%40lizworthey)](https://twitter.com/lizworthey)
        - Email: <lworthey@uab.edu>
        - GitHub: https://github.com/uab-cgds-worthey
        """,
    )
    right_info_col.markdown(
        """
        ### Acknowledgements
        - [OpenCravat - run.opencravat.org](https://run.opencravat.org/)
        - [ClinVar - www.ncbi.nlm.nih.gov/clinvar/](https://www.ncbi.nlm.nih.gov/clinvar/)
        - [SHAP - shap.readthedocs.io](https://shap.readthedocs.io/)
        """
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
            GNU General Public License v3.0
            """
    )

    st.markdown("---")
    foot_col1, foot_col2, foot_col3 = st.columns((1.5, 1, 1))
    foot_col1.markdown(
        "Developed and Maintained by [Tarun Mamidi](https://www.linkedin.com/in/tkmamidi/)"
    )
    foot_col3.markdown(
        "[Center for Computational Genomics and Data Science](https://sites.uab.edu/cgds/)"
    )
    foot_col2.markdown("Copyright (c) 2023 CGDS")


if __name__ == "__main__":
    main()
