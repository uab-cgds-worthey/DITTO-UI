import streamlit as st

# Config the whole app
st.set_page_config(
    page_title="DITTO4NF",
    page_icon="🧊",
    layout="wide",  # initial_sidebar_state="expanded",
)


def sidebar_links():
    database_link_dict = {
        "GitHub Page": "https://github.com/uab-cgds-worthey/DITTO4NF",
        "RCSB Protein Data Bank": "https://www.rcsb.org",
    }

    st.sidebar.markdown("## Database-Related Links")
    for link_text, link_url in database_link_dict.items():
        st.sidebar.markdown(f"[{link_text}]({link_url})")

    software_link_dict = {
        "3Dmol": "https://3dmol.csb.pitt.edu",
        "Pandas": "https://pandas.pydata.org",
        "SHAP": "https://shap.readthedocs.io/en/latest/index.html",
        "Matplotlib": "https://matplotlib.org",
        "Streamlit": "https://streamlit.io",
    }

    st.sidebar.markdown("## Software-Related Links")
    link_1_col, link_2_col, link_3_col = st.sidebar.columns(3)
    i = 0
    link_col_dict = {0: link_1_col, 1: link_2_col, 2: link_3_col}
    for link_text, link_url in software_link_dict.items():
        st_col = link_col_dict[i]
        i += 1
        if i == len(link_col_dict.keys()):
            i = 0
        st_col.markdown(f"[{link_text}]({link_url})")


st.markdown("# DITTO")
st.markdown("\n\n")
st.markdown(
    "### A tool for exploring likely pathogenic variants and their predicted functional impact."
)
st.markdown("\n\n")
st.markdown(
    "**Created by [Tarun Mamidi](https://www.linkedin.com/in/tkmamidi/) and"
    " [Liz Worthey](https://www.linkedin.com/in/lizworthey/)**"
)
st.markdown("\n\n")
st.markdown("\n\n")
st.markdown("**[Center for Computational Genomics and Data Science](https://sites.uab.edu/cgds/)**")

sidebar_links()

st.markdown("---")

left_info_col, right_info_col = st.columns(2)
left_info_col.markdown(
    f"""
    ### Authors
    Please feel free to contact us with any issues, comments, or questions.""",
)
left_info_col.markdown(
    f"""
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
st.markdown("Copyright (c) 2023 CGDS")
