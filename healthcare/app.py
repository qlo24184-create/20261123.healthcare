import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="醫療資料可視化儀表板｜基本資料",
    page_icon="🏥",
    layout="wide",
)


@st.cache_data
def load_data(csv_path: str = "data.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["性別"] = df["Gender"].map({0: "男性", 1: "女性"}).fillna("未知")
    df["年齡區間"] = pd.cut(
        df["Age"],
        bins=[0, 29, 44, 59, 74, 120],
        labels=["13-29歲", "30-44歲", "45-59歲", "60-74歲", "75-89歲"],
        right=True,
    ).astype(str)
    return df


try:
    df = load_data()
except FileNotFoundError:
    st.error("找不到 `data.csv`，請確認檔案與 `app.py` 位於同一資料夾。")
    st.stop()

# ---------------------------------------------------------
# 左側欄位：下拉式基本資料選單（不含血型）
# ---------------------------------------------------------
with st.sidebar:
    st.header("基本資料篩選選單")
    st.caption("選擇條件後，右側指標與圖表將即時更新")

    gender_options = ["全部", "男性", "女性"]
    selected_gender = st.selectbox("性別（Gender）", gender_options, index=0, key="gender_select_1")

    admission_options = ["全部"] + sorted(df["Admission Type"].dropna().unique().tolist())
    selected_admission = st.selectbox("入院方式（Admission Type）", admission_options, index=0)

    age_group_options = ["全部", "13-29歲", "30-44歲", "45-59歲", "60-74歲", "75-89歲"]
    selected_age_group = st.selectbox("年齡區間（Age Group）", age_group_options, index=0)

    exclude_negative = st.checkbox("排除負帳務金額（Billing Amount < 0）", value=False)

    if st.button("重設所有篩選條件", use_container_width=True):
        st.rerun()

# 套用篩選條件
filtered_df = df.copy()
if selected_gender != "全部":
    filtered_df = filtered_df[filtered_df["性別"] == selected_gender]
if selected_admission != "全部":
    filtered_df = filtered_df[filtered_df["Admission Type"] == selected_admission]
if selected_age_group != "全部":
    filtered_df = filtered_df[filtered_df["年齡區間"] == selected_age_group]
if exclude_negative:
    filtered_df = filtered_df[filtered_df["Billing Amount"] >= 0]

# ---------------------------------------------------------
# 主畫面：第一頁內容
# ---------------------------------------------------------
st.title("🏥 醫療紀錄簡易可視化儀表板 — 第一頁：基本資料總覽")
st.markdown(
    f"目前篩選條件：**性別＝{selected_gender}**｜"
    f"**入院方式＝{selected_admission}**｜**年齡區間＝{selected_age_group}**"
)

if filtered_df.empty:
    st.warning("目前篩選條件下沒有符合的資料，請調整左側下拉式選單。")
    st.stop()

# KPI 指標列
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("篩選筆數", f"{len(filtered_df):,}", f"佔全體 {len(filtered_df) / len(df) * 100:.1f}%")
kpi2.metric("平均年齡", f"{filtered_df['Age'].mean():.1f} 歲", f"中位數 {filtered_df['Age'].median():.0f} 歲")
kpi3.metric(
    "平均帳務金額",
    f"{filtered_df['Billing Amount'].mean():,.2f}",
    f"中位數 {filtered_df['Billing Amount'].median():,.2f}",
)
neg_count = int((filtered_df["Billing Amount"] < 0).sum())
kpi4.metric("負帳務筆數", f"{neg_count:,}", "帳務小於 0 筆數")

st.divider()

# 圖表第一列：性別分佈 & 年齡區間分佈
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("性別分佈（0＝男性，1＝女性）")
    gender_summary = (
        filtered_df.groupby("性別", as_index=False)
        .agg(筆數=("Name", "count"), 平均費用=("Billing Amount", "mean"))
    )
    fig_gender = px.bar(
        gender_summary,
        x="性別",
        y="筆數",
        color="性別",
        text="筆數",
        hover_data={"平均費用": ":.2f"},
        title="各性別紀錄筆數",
    )
    fig_gender.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig_gender.update_layout(showlegend=False, yaxis_title="筆數", xaxis_title="性別")
    st.plotly_chart(fig_gender, use_container_width=True)

with col_right:
    st.subheader("年齡區間分佈")
    order_list = ["13-29歲", "30-44歲", "45-59歲", "60-74歲", "75-89歲"]
    age_summary = (
        filtered_df["年齡區間"]
        .value_counts()
        .reindex(order_list, fill_value=0)
        .reset_index()
        .rename(columns={"年齡區間": "年齡區間", "count": "筆數"})
    )
    fig_age = px.bar(
        age_summary,
        x="年齡區間",
        y="筆數",
        text="筆數",
        title="各年齡區間紀錄筆數",
    )
    fig_age.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig_age.update_layout(yaxis_title="筆數", xaxis_title="年齡區間")
    st.plotly_chart(fig_age, use_container_width=True)

# 圖表第二列：入院方式佔比 & 入院方式平均費用
col_l2, col_r2 = st.columns(2)

with col_l2:
    st.subheader("入院方式佔比")
    adm_summary = (
        filtered_df.groupby("Admission Type", as_index=False)
        .agg(筆數=("Name", "count"), 平均費用=("Billing Amount", "mean"))
    )
    fig_adm_pie = px.pie(
        adm_summary,
        names="Admission Type",
        values="筆數",
        hole=0.35,
        title="入院方式筆數佔比",
    )
    st.plotly_chart(fig_adm_pie, use_container_width=True)

with col_r2:
    st.subheader("各入院方式平均帳務金額")
    fig_adm_bill = px.bar(
        adm_summary.sort_values("平均費用", ascending=False),
        x="Admission Type",
        y="平均費用",
        color="Admission Type",
        text="平均費用",
        hover_data={"筆數": ":,"},
        title="不同入院方式的平均帳務金額",
    )
    fig_adm_bill.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_adm_bill.update_layout(showlegend=False, xaxis_title="入院方式", yaxis_title="平均帳務金額")
    st.plotly_chart(fig_adm_bill, use_container_width=True)

# 明細資料預覽（不含血型欄位）
st.subheader("篩選後基本資料明細（前 100 筆）")
display_cols = [
    "Name",
    "Age",
    "性別",
    "年齡區間",
    "Admission Type",
    "Medical Condition",
    "Medication",
    "Billing Amount",
]
st.dataframe(
    filtered_df[display_cols].head(100),
    use_container_width=True,
    hide_index=True,
)

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="醫療資料可視化儀表板｜疾病、用藥、費用",
    page_icon="💊",
    layout="wide",
)


@st.cache_data
def load_data(csv_path: str = "data.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["性別"] = df["Gender"].map({0: "男性", 1: "女性"}).fillna("未知")
    return df


try:
    df = load_data()
except FileNotFoundError:
    st.error("找不到 `data.csv.csv`，請確認檔案位於專案根目錄。")
    st.stop()

# ---------------------------------------------------------
# 側邊欄篩選：疾病、用藥、性別、入院方式
# ---------------------------------------------------------
with st.sidebar:
    st.header("疾病・用藥・費用篩選")

    cond_list = ["全部"] + sorted(df["Medical Condition"].dropna().unique().tolist())
    selected_cond = st.selectbox("疾病（Medical Condition）", cond_list, index=0)

    med_list = ["全部"] + sorted(df["Medication"].dropna().unique().tolist())
    selected_med = st.selectbox("用藥（Medication）", med_list, index=0)

    gender_list = ["全部", "男性", "女性"]
    selected_gender = st.selectbox("性別", gender_list, index=0, key="gender_selectbox_1")

    adm_list = ["全部"] + sorted(df["Admission Type"].dropna().unique().tolist())
    selected_adm = st.selectbox(
    "入院方式（Admission Type）", 
    adm_list, 
    index=0,
    key="adm_type_select"  # 👈 加上這行（名稱可自訂，只要全程式唯一即可）
)

exclude_negative = st.checkbox(
    "排除負帳務金額（Billing Amount < 0）", 
    value=False,
    key="exclude_neg_checkbox"  # 👈 順便也給 checkbox 加上，避免下一個報錯
)

filtered_df = df.copy()
if selected_cond != "全部":
    filtered_df = filtered_df[filtered_df["Medical Condition"] == selected_cond]
if selected_med != "全部":
    filtered_df = filtered_df[filtered_df["Medication"] == selected_med]
if selected_gender != "全部":
    filtered_df = filtered_df[filtered_df["性別"] == selected_gender]
if selected_adm != "全部":
    filtered_df = filtered_df[filtered_df["Admission Type"] == selected_adm]
if exclude_negative:
    filtered_df = filtered_df[filtered_df["Billing Amount"] >= 0]

# ---------------------------------------------------------
# 主畫面：第二頁內容
# ---------------------------------------------------------
st.title("💊 醫療紀錄簡易可視化儀表板 — 第二頁：疾病、用藥、費用")
st.markdown(
    f"目前篩選：**疾病＝{selected_cond}**｜**用藥＝{selected_med}**｜"
    f"**性別＝{selected_gender}**｜**入院方式＝{selected_adm}**"
)

if filtered_df.empty:
    st.warning("目前篩選條件下無符合資料，請調整左側選單。")
    st.stop()

# KPI 指標
m1, m2, m3, m4 = st.columns(4)
m1.metric("符合筆數", f"{len(filtered_df):,}")
m2.metric("平均帳務金額", f"{filtered_df['Billing Amount'].mean():,.2f}")
m3.metric("中位數帳務金額", f"{filtered_df['Billing Amount'].median():,.2f}")
m4.metric("平均年齡", f"{filtered_df['Age'].mean():.1f} 歲")

st.divider()

# 第一列圖表：各疾病平均費用 & 疾病×用藥平均費用熱圖
c1, c2 = st.columns(2)

with c1:
    st.subheader("各疾病平均帳務金額")
    cond_bill = (
        filtered_df.groupby("Medical Condition", as_index=False)
        .agg(
            筆數=("Billing Amount", "count"),
            平均費用=("Billing Amount", "mean"),
            中位數費用=("Billing Amount", "median"),
            平均年齡=("Age", "mean"),
        )
        .sort_values("平均費用", ascending=False)
    )
    fig_cond_bill = px.bar(
        cond_bill,
        x="Medical Condition",
        y="平均費用",
        color="Medical Condition",
        text="平均費用",
        hover_data={"筆數": ":,", "中位數費用": ":,.2f", "平均年齡": ":.1f"},
        title="疾病平均帳務金額比較",
    )
    fig_cond_bill.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_cond_bill.update_layout(showlegend=False, xaxis_title="疾病", yaxis_title="平均帳務金額")
    st.plotly_chart(fig_cond_bill, use_container_width=True)

with c2:
    st.subheader("疾病 × 用藥 平均帳務金額熱圖")
    piv_bill = filtered_df.pivot_table(
        index="Medical Condition",
        columns="Medication",
        values="Billing Amount",
        aggfunc="mean",
    )
    fig_heat = px.imshow(
        piv_bill,
        text_auto=",.0f",
        aspect="auto",
        color_continuous_scale="YlGnBu",
        title="疾病與用藥組合之平均帳務金額",
    )
    fig_heat.update_layout(xaxis_title="用藥", yaxis_title="疾病")
    st.plotly_chart(fig_heat, use_container_width=True)

# 第二列圖表：疾病×用藥 筆數堆疊 & 高低平均費用組合排行
c3, c4 = st.columns(2)

with c3:
    st.subheader("各疾病用藥筆數分佈")
    cm_counts = (
        filtered_df.groupby(["Medical Condition", "Medication"], as_index=False)
        .agg(筆數=("Name", "count"), 平均費用=("Billing Amount", "mean"))
    )
    fig_stack = px.bar(
        cm_counts,
        x="Medical Condition",
        y="筆數",
        color="Medication",
        barmode="stack",
        hover_data={"平均費用": ":,.2f"},
        title="疾病與用藥筆數分佈",
    )
    fig_stack.update_layout(xaxis_title="疾病", yaxis_title="筆數")
    st.plotly_chart(fig_stack, use_container_width=True)

with c4:
    st.subheader("疾病 × 用藥 組合平均費用排行（Top / Bottom）")
    combo_table = (
        filtered_df.groupby(["Medical Condition", "Medication"], as_index=False)
        .agg(
            筆數=("Name", "count"),
            平均年齡=("Age", "mean"),
            平均費用=("Billing Amount", "mean"),
            中位數費用=("Billing Amount", "median"),
        )
        .sort_values("平均費用", ascending=False)
    )
    top_bottom = pd.concat([combo_table.head(5), combo_table.tail(5)], ignore_index=True)
    top_bottom["組合"] = top_bottom["Medical Condition"] + " + " + top_bottom["Medication"]

    fig_combo = px.bar(
        top_bottom.sort_values("平均費用", ascending=True),
        x="平均費用",
        y="組合",
        orientation="h",
        text="平均費用",
        hover_data={"筆數": ":,", "平均年齡": ":.1f", "中位數費用": ":,.2f"},
        title="平均帳務金額最高 5 組 vs. 最低 5 組",
    )
    fig_combo.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_combo.update_layout(xaxis_title="平均帳務金額", yaxis_title="疾病 × 用藥組合")
    st.plotly_chart(fig_combo, use_container_width=True)

# 彙總統計表
st.subheader("疾病 × 用藥 交叉統計明細")
st.dataframe(
    combo_table.style.format({
        "筆數": "{:,}",
        "平均年齡": "{:.2f}",
        "平均費用": "{:,.2f}",
        "中位數費用": "{:,.2f}",
    }),
    use_container_width=True,
    hide_index=True,
)