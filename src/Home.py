import streamlit as st

# Config the whole app
st.set_page_config(
    page_title="DITTO4NF",
    page_icon="🧊",
    layout="wide",  # initial_sidebar_state="expanded",
)

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
