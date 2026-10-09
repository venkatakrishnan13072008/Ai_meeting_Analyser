import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
import re
from datetime import datetime
import random

st.set_page_config(page_title="Meeting Effectiveness Analyzer", layout="wide", page_icon="🎙️")
st.title("🎙️ AI-Based Meeting Effectiveness Analysis")
st.markdown("Analyze speech patterns, interactions, sentiment & topics")

st.sidebar.header("📁 Meeting Input")
input_mode = st.sidebar.radio("Input Type", ["Simulated Demo Meeting", "Paste Transcript", "Upload Transcript (.txt)"])

def generate_demo_data():
    speakers = ["Alex (PM)", "Priya (Dev)", "John (Design)", "Sara (QA)"]
    lines = []
    start = 0
    for i in range(40):
        spk = random.choice(speakers)
        dur = random.randint(10, 45)
        pool = [
            "We need to discuss Project Timeline in detail.",
            "I think we are on track but need more clarity on Budget.",
            "That's a great point! I agree with that approach.",
            "Sorry to interrupt, but I have a concern here.",
            "The deadline is tight, we need to prioritize UI work.",
            "Overall positive progress, but Testing is pending.",
            "I feel this is not working, need to revisit Design.",
            "Action item: Alex will update the timeline.",
            "Decision made: We will go with Option A for Deployment."
        ]
        txt = random.choice(pool)
        if random.random() < 0.15:
            txt = "[INTERRUPTION] " + txt
        lines.append({"time": start, "speaker": spk, "text": txt, "duration": dur})
        start += dur + random.randint(2,8)
    return lines

if 'data' not in st.session_state:
    st.session_state['data'] = generate_demo_data()

transcript_data = []
if input_mode == "Simulated Demo Meeting":
    if st.sidebar.button("Generate New Demo Meeting"):
        st.session_state['data'] = generate_demo_data()
    transcript_data = st.session_state['data']
elif input_mode == "Paste Transcript":
    raw = st.sidebar.text_area("Paste", "Alex: We need to finalize timeline\nPriya: I agree\nJohn: Design pending", height=200)
    if raw:
        t=0
        for line in raw.strip().split('\n'):
            if ':' in line:
                spk, txt = line.split(':',1)
                transcript_data.append({"time": t, "speaker": spk.strip(), "text": txt.strip(), "duration": len(txt.split())*2})
                t+=10
else:
    file = st.sidebar.file_uploader("Upload .txt", type=['txt'])
    if file:
        content = file.read().decode('utf-8')
        t=0
        for line in content.strip().split('\n'):
            if ':' in line:
                spk, txt = line.split(':',1)
                transcript_data.append({"time": t, "speaker": spk.strip(), "text": txt.strip(), "duration": len(txt.split())*2})
                t+=10

if not transcript_data:
    st.warning("Provide data")
    st.stop()

df = pd.DataFrame(transcript_data)
stats = df.groupby('speaker').agg(speaking_time=('duration','sum'), turns=('speaker','count')).reset_index()
total_time = stats['speaking_time'].sum()
stats['participation_rate'] = (stats['speaking_time']/total_time*100).round(1)
df['is_interruption'] = df['text'].str.contains("INTERRUPTION|sorry to interrupt", case=False)
interrupt_df = df.groupby('speaker')['is_interruption'].sum().reset_index()

def get_sent(txt):
    tl = txt.lower()
    pos = ['great','agree','good','positive','on track','excellent']
    neg = ['concern','blocked','not working','tight','pending','issue']
    p = sum(1 for w in pos if w in tl)
    n = sum(1 for w in neg if w in tl)
    return 'Positive' if p>n else 'Negative' if n>p else 'Neutral'

df['sentiment'] = df['text'].apply(get_sent)

st.subheader("📊 Metrics")
c1,c2,c3,c4 = st.columns(4)
c1.metric("Duration", f"{total_time//60}m {total_time%60}s")
c2.metric("Participants", df['speaker'].nunique())
c3.metric("Turns", len(df))
c4.metric("Interruptions", int(df['is_interruption'].sum()))

avg = 100/df['speaker'].nunique()
imb = abs(stats['participation_rate'] - avg).mean()
eff = max(0, 100 - imb*1.5 - df['is_interruption'].sum()*2)
st.progress(int(eff))
st.caption(f"Effectiveness: {eff:.1f}/100")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(px.pie(stats, values='speaking_time', names='speaker', hole=0.4), use_container_width=True)
with col2:
    st.plotly_chart(px.bar(stats, x='speaker', y='participation_rate', color='speaker', text='participation_rate'), use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(px.scatter(df, x='time', y='speaker', size='duration', color='sentiment', hover_data=['text']), use_container_width=True)
with col4:
    sc = df['sentiment'].value_counts().reset_index()
    sc.columns=['sentiment','count']
    st.plotly_chart(px.bar(sc, x='sentiment', y='count', color='sentiment'), use_container_width=True)

st.dataframe(df, use_container_width=True)
st.download_button("Download CSV", df.to_csv(index=False).encode('utf-8'), "report.csv", "text/csv")
