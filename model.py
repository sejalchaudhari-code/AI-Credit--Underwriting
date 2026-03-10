import pandas as pd
from sklearn.linear_model import LogisticRegression

data = {
    "revenue":[50,40,30,20,10,60,80],
    "debt":[20,30,40,35,15,25,30],
    "networth":[40,30,20,15,10,50,60],
    "default":[0,0,1,1,1,0,0]
}

df = pd.DataFrame(data)

X = df[["revenue","debt","networth"]]
y = df["default"]

model = LogisticRegression()
model.fit(X,y)

def predict_default(revenue,debt,networth):
    prob = model.predict_proba([[revenue,debt,networth]])[0][1]
    return prob