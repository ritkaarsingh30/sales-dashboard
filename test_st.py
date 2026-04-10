import streamlit as st

t1, t2 = st.tabs(["A", "B"])
with t1:
    st.write("A")
    t3, t4 = st.tabs(["C", "D"])
    with t3:
        st.write("C")
