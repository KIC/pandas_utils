# pandas-ml-utils

I was really sick of converting data frames to numpy arrays back and forth just to try out a 
 simple logistic regression. So I have started a pandas ml utilities library where
 everything should be reachable from the data frame itself. Check out the following examples
 to see what I mean by that.

## Fitting

### Ordinary Binary Classification
```python
import pandas as pd
import pandas_ml_utils as pmu
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression

bc = load_breast_cancer()

df = pd.DataFrame(bc.data, columns = bc.feature_names)
df["label"] = bc.target


fit = df.fit_classifier(pmu.SkitModel(LogisticRegression(solver='lbfgs', max_iter=300),
                                      pmu.FeaturesAndLabels(features=['mean radius', 'mean texture', 'mean perimeter', 'mean area', 
                                                                      'worst concave points', 'worst fractal dimension'],
                                                            labels=['label'])),
                        test_size=0.4)
``` 

As a result you get a Fit object which holds the fitted model and two ClassificationSummary.
 One for the training data and one for the test Data. In case of the classification was
 executed in a notebook you get a nice table:

![Fit](./images/simple-fit.png)

### Binary Classification with Loss
As you can see in the above example are two confusion matrices the regular well known one 
 and a "loss". The intend of loss matrix is to tell you if a miss classification has a cost
 i.e. a loss in dollars. 
```python
import pandas as pd
import pandas_ml_utils as pmu
from sklearn.linear_model import LogisticRegression

df = pd.fetch_yahoo(spy='SPY')
df["label"] = df["spy_Close"] > df["spy_Open"]
df["loss"] = (df["spy_Open"] / df["spy_Close"] - 1) * 100

fit = df.fit_classifier(pmu.SkitModel(LogisticRegression(solver='lbfgs'),
                                      pmu.FeaturesAndLabels(features=['spy_Open', 'spy_Low'],
                                                            labels=['label'],
                                                            loss_column='loss')),
                        test_size=0.4)
```

![Fit with loss](./images/fit-with-loss.png)
         
Now you can see the loss in % of dollars of your miss classification. The classification
 probabilities are plotted on the very top of the plot.

### Auto-Regressive Models and RNN Shape
It is also possible to use the FeaturesAndLabels object to generate a auto regressive 
 features. By default lagging features results in an RNN shape as Keras likes to have it.
 However we can also use SkitModels the features will be implicitly transformed back 
 into a 2D array.  

```python
import pandas_ml_utils as pmu
pmu.FeaturesAndLabels(features=['feature'],
                      labels=['label'],
                      feature_lags=range(0, 10))
```

One may like to use very long lags i.e. to catch seasonal effects. Since very long lags
are a bit fuzzy I usually like to smooth them a bit by using simple averages.

```python
import pandas_ml_utils as pmu
pmu.FeaturesAndLabels(features=['feature'], 
                      labels=['label'], 
                      target_columns=['strike'],
                      loss_column='put_loss',
                      feature_lags=[0, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233],
                      lag_smoothing={
                          6: lambda df: df.SMA(3, price=df.columns[0]),
                          35: lambda df: df.SMA(5, price=df.columns[0])
                      })
```

Every lag from 6 onwards will be smoothed by a 3 period average, every lag from 35 onwards
 with a 5 periods moving average.
 
## Back-Testing a Model
todo ...

## Save, load reuse a Model
To save a model you simply call the save method on the model inside of the fit.
```
fit.model.save('/tmp/foo.model')
```

Loading is as simply as calling load on the Model object. You can immediately apply
 the model on the dataframe to get back the features along with the classification
 (which is just another data frame).

```python

import pandas as pd
import pandas_ml_utils as pmu
from sklearn.datasets import load_breast_cancer

bc = load_breast_cancer()
df = pd.DataFrame(bc.data, columns = bc.feature_names)

df.classify(pmu.Model.load('/tmp/foo.model')).tail()
```  

NOTE If you have a target level for your binary classifier like all houses cheaper then
 50k then you can define this target level to the FeaturesAndLabels object likes so:
 `FeaturesAndLabels(target_columns=['House Price'])`. This target column is simply fed 
 through to the classified dataframe as target columns.
 
### Other utility objects
TODO describe ...
* LazyDataFrame
* HashableDataFrame


## TODO

* rename pandas util to pandas ml utils and use pmu as abbreviation
* multi model is just another implementation of model
* add horizontal line at prob. cutoff https://stackoverflow.com/a/12864466/1298461
  to the chart

## Wanna help?
* currently I only need binary classification, maybe you want to enable multiple
  classification categories.     
* write some tests