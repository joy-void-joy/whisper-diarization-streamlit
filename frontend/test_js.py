import streamlit as st
from streamlit_javascript import st_javascript

st.subheader("Javascript API call!")

return_value = st_javascript("""window.location.assign("https://google.com")""")

st.markdown(f"Return value was: {return_value}")
