import plotly.express as px
import pandas as pd

df = pd.DataFrame({"A": [10, 5], "B": ["X", "Y"]})
fig = px.bar(df, x="A", y="B", text=["10", "5"], color="A", color_continuous_scale="Blues")
fig.update_traces(
    textfont=dict(color=[None, "#E0E0E0"])
)
fig.write_html("test.html")
print("Success")
