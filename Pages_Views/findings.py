import streamlit as st


def render_findings_page():
    """Static, read-only summary of findings from the UK Online Retail analysis."""

    st.markdown(
        """
        <div class="page-kicker">Research Summary</div>
        <div class="page-title">Key Findings</div>
        <div class="page-sub">
            A consolidated readout of the major patterns, supporting findings,
            and data-quality considerations identified across the UK Online Retail project.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # Explicitly communicate that this page is an editorial summary, not a live dashboard.
    st.html(
        """
        <div style="display:flex;gap:12px;align-items:flex-start;padding:15px 18px;
                    border:1px solid #ead9a7;border-radius:14px;background:#fff9e9;
                    color:#6b5520;margin-bottom:20px;">
            <div style="font-size:20px;line-height:1;">ⓘ</div>
            <div>
                <div style="font-weight:750;font-size:14px;margin-bottom:4px;">
                    Read-only findings page
                </div>
                <div style="font-size:13px;line-height:1.55;">
                    This page is a static summary of the full-dataset analysis. It is not
                    interactive: dashboard filters do not apply here, and the findings
                    do not recalculate when selections change.
                </div>
            </div>
        </div>
        """
    )

    # Snapshot metrics from the completed analysis. These are intentionally static.
    st.markdown(
        '<div class="section-title">Analysis Snapshot</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        from Components.kpi_cards import render_kpi_card
        render_kpi_card("Sales Revenue", "£19.67M", "Sale transactions · full dataset", featured=True)
    with c2:
        render_kpi_card("Sale Orders", "39,580", "Distinct sale invoices")
    with c3:
        render_kpi_card("Identified Customers", "5,862", "Customers with an ID")
    with c4:
        render_kpi_card("Units Sold", "11.19M", "Across sale transactions")

    st.write("")
    st.markdown(
        '<div class="section-title">Major Findings</div>',
        unsafe_allow_html=True,
    )

    st.html(
        """
        <style>
          .finding-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:8px 0 22px;}
          .finding-card{background:#fff;border:1px solid #e3e7e1;border-radius:17px;padding:21px 22px;box-shadow:0 2px 8px rgba(20,45,30,.025);}
          .finding-card.featured{background:#176f49;color:#fff;border-color:#176f49;}
          .finding-tag{font-size:10px;letter-spacing:1.2px;text-transform:uppercase;font-weight:800;color:#6e8d77;margin-bottom:10px;}
          .finding-card.featured .finding-tag{color:#c5e5d2;}
          .finding-title{font-size:18px;font-weight:750;line-height:1.3;margin-bottom:9px;color:#18251d;}
          .finding-card.featured .finding-title{color:#fff;}
          .finding-metric{font-size:28px;line-height:1.15;font-weight:800;color:#18764d;margin:2px 0 10px;}
          .finding-card.featured .finding-metric{color:#fff;}
          .finding-body{font-size:13px;line-height:1.65;color:#65736a;}
          .finding-card.featured .finding-body{color:#e2f1e8;}
          .finding-foot{border-top:1px solid #e9eee9;margin-top:14px;padding-top:11px;font-size:11px;line-height:1.5;color:#849087;}
          .finding-card.featured .finding-foot{border-color:rgba(255,255,255,.2);color:#d0e8d9;}
          .minor-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:8px 0 22px;}
          .minor-card{background:#fff;border:1px solid #e3e7e1;border-radius:15px;padding:17px 18px;}
          .minor-label{font-size:11px;font-weight:750;color:#718078;text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px;}
          .minor-value{font-size:23px;font-weight:800;color:#1c704b;margin-bottom:7px;}
          .minor-text{font-size:12px;line-height:1.6;color:#6c7971;}
          .finding-section-note{font-size:12px;color:#7d8880;margin:-2px 0 12px;}
          .caveat-list{background:#fff;border:1px solid #e3e7e1;border-radius:15px;padding:18px 22px;margin:8px 0 18px;}
          .caveat-list ul{margin:0;padding-left:19px;color:#65736a;font-size:13px;line-height:1.8;}
          @media(max-width:750px){.finding-grid{grid-template-columns:1fr}.minor-grid{grid-template-columns:1fr}}
        </style>

        <div class="finding-grid">
          <div class="finding-card featured">
            <div class="finding-tag">01 · Market concentration</div>
            <div class="finding-title">Revenue is heavily concentrated in a small group of markets</div>
            <div class="finding-metric">95.04%</div>
            <div class="finding-body">The top five countries account for approximately 95.04% of total sales revenue. The United Kingdom is the leading market, so overall performance is strongly shaped by UK demand.</div>
            <div class="finding-foot">Implication: report UK performance separately from international markets to avoid masking smaller-market movement.</div>
          </div>

          <div class="finding-card">
            <div class="finding-tag">02 · Customer loyalty</div>
            <div class="finding-title">Repeat purchasing is a meaningful part of the customer base</div>
            <div class="finding-metric">72.26%</div>
            <div class="finding-body">About 72.26% of identified customers placed at least two distinct orders during the analyzed period. This indicates substantial repeat purchasing among customers whose IDs are available.</div>
            <div class="finding-foot">Interpretation applies to identified customers and the full analysis period—not anonymous transactions.</div>
          </div>

          <div class="finding-card">
            <div class="finding-tag">03 · Customer concentration</div>
            <div class="finding-title">Top customers contribute a noticeable, but not dominant, revenue share</div>
            <div class="finding-metric">14.06%</div>
            <div class="finding-body">The top 10 identified customers contribute approximately 14.06% of total revenue. Revenue is distributed beyond only a handful of high-value customers, while key accounts still merit attention.</div>
            <div class="finding-foot">Customer-level concentration excludes transactions without a customer ID.</div>
          </div>

          <div class="finding-card">
            <div class="finding-tag">04 · Product concentration</div>
            <div class="finding-title">Revenue is spread across a broad catalog</div>
            <div class="finding-metric">~8.0%</div>
            <div class="finding-body">The top 10 products contribute roughly 8% of total sales revenue. No small top-10 group accounts for most revenue, making the wider product range relevant to performance.</div>
            <div class="finding-foot">Product rankings use sales revenue; high-volume products are not necessarily the highest-revenue products.</div>
          </div>
        </div>
        """
    )

    st.markdown(
        '<div class="section-title">Supporting & Minor Findings</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="finding-section-note">Additional signals that add context to the headline findings.</div>',
        unsafe_allow_html=True,
    )

    st.html(
        """
        <div class="minor-grid">
          <div class="minor-card">
            <div class="minor-label">Repeat activity</div>
            <div class="minor-value">27.74%</div>
            <div class="minor-text">The remaining identified customers are one-time buyers within the analysis window. This is a useful segment for retention-focused follow-up, while recognizing that the observation period affects the measure.</div>
          </div>
          <div class="minor-card">
            <div class="minor-label">Returns / adjustments</div>
            <div class="minor-value">0.34%</div>
            <div class="minor-text">Adjustment/return rows are approximately 0.34% of sale rows. This is a row-count comparison, not a returned-order rate or a monetary loss percentage.</div>
          </div>
          <div class="minor-card">
            <div class="minor-label">Catalog coverage</div>
            <div class="minor-value">4,910</div>
            <div class="minor-text">Distinct products appear in sale transactions. Product mix and contribution can therefore be examined across a substantial assortment.</div>
          </div>
          <div class="minor-card">
            <div class="minor-label">Order economics</div>
            <div class="minor-value">£496.95</div>
            <div class="minor-text">Average order value across sale invoices. It is a revenue-per-invoice measure and can be influenced by bulk purchases and high-quantity orders.</div>
          </div>
          <div class="minor-card">
            <div class="minor-label">International context</div>
            <div class="minor-value">~4.96%</div>
            <div class="minor-text">Markets outside the top five collectively account for about 4.96% of revenue, based on the top-five concentration measure.</div>
          </div>
          <div class="minor-card">
            <div class="minor-label">Analysis window</div>
            <div class="minor-value">2009–2011</div>
            <div class="minor-text">The dataset spans December 2009 through December 2011. Findings describe this historical period and should not be read as current retail-market conditions.</div>
          </div>
        </div>
        """
    )

    st.markdown(
        '<div class="section-title">Data Quality & Interpretation Notes</div>',
        unsafe_allow_html=True,
    )

    st.html(
        """
        <div class="caveat-list">
          <ul>
            <li><b>Customer IDs:</b> approximately 240,000 raw records had missing customer IDs. Customer metrics therefore represent identified customers, not every transaction or shopper.</li>
            <li><b>Product descriptions:</b> approximately 3,000 records had missing product descriptions. Product-ID-based analysis remains useful, but descriptive labels may be incomplete.</li>
            <li><b>Data preparation:</b> duplicate records were removed before analysis; the working dataset contains 1,033,036 rows.</li>
            <li><b>Transaction types:</b> sales, cancellations, returns/adjustments, and special transaction types are treated separately. Row-based operational rates should not be confused with order-level or value-based rates.</li>
            <li><b>Scope:</b> this is a historical UK online retail dataset covering Dec 2009–Dec 2011. Results are descriptive, not causal, and may not generalize to present-day retail.</li>
          </ul>
        </div>
        """
    )

    st.html(
        """
        <div style="background:#edf5ef;border:1px solid #d7e8db;border-radius:14px;padding:16px 19px;margin-top:8px;">
          <div style="font-size:13px;font-weight:800;color:#245f40;margin-bottom:5px;">Bottom line</div>
          <div style="font-size:13px;line-height:1.65;color:#4e6d59;">
            The analysis points to a UK-led revenue base, substantial repeat purchasing among identified customers,
            and a broad product contribution profile. These findings should be read alongside the dataset's
            historical scope and customer-ID limitations.
          </div>
        </div>
        """
    )
