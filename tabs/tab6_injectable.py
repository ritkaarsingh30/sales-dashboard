"""
Tab 6 — Injectable Commission (placeholder)
"""

import streamlit as st


def render_tab6():
    st.markdown(
        """
        <div style="display:flex;align-items:center;justify-content:center;
                    min-height:480px;">
            <div style="background:linear-gradient(135deg,#12192a,#1a2640);
                        border:1px solid #2a4060;border-radius:20px;
                        padding:56px 72px;text-align:center;max-width:560px;
                        box-shadow: 0 8px 32px rgba(76,159,255,0.12);">
                <div style="font-size:64px;margin-bottom:20px;">💉</div>
                <h2 style="color:#4C9FFF;font-size:28px;margin:0 0 12px 0;">
                    Injectable Commission ROI
                </h2>
                <div style="display:inline-block;background:#1e3050;
                            border-radius:20px;padding:6px 18px;
                            color:#B57BFF;font-size:13px;font-weight:600;
                            letter-spacing:1px;margin-bottom:20px;">
                    COMING SOON
                </div>
                <p style="color:#8899aa;font-size:15px;line-height:1.7;margin:0;">
                    This tab will display injectable product commission ROI analysis —
                    including 12-month commission trends per clinic, product-level
                    profitability, and MR attribution breakdowns.<br><br>
                    Upload <strong style="color:#cce0ff;">INJECTABLE_COMISSION_TILL_feb_2026_IVC.xlsx</strong>
                    when ready to activate.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
