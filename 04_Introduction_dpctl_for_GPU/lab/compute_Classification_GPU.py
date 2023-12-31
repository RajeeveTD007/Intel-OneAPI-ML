# Copyright 2022 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from sklearn import metrics
from sklearn.model_selection import train_test_split
from sklearn.datasets import fetch_openml
import pandas as pd

############################3 import dpctl #################################

import dpctl
print(dpctl.__version__)

############################################################################

#########  apply patch here  prior to import of desired scikit-learn #######
from sklearnex import patch_sklearn
patch_sklearn()
############################################################################


from  sklearn.datasets import fetch_covtype
x, y = fetch_covtype(return_X_y=True)
# Data Set Information:
# Predicting forest cover type from cartographic variables only (no remotely sensed data). The actual forest cover type for a given observation (30 x 30 meter cell) was determined from US Forest Service (USFS) Region 2 Resource Information System (RIS) data. Independent variables were derived from data originally obtained from US Geological Survey (USGS) and USFS data. Data is in raw form (not scaled) and contains binary (0 or 1) columns of data for qualitative independent variables (wilderness areas and soil types).
# This study area includes four wilderness areas located in the Roosevelt National Forest of northern Colorado. These areas represent forests with minimal human-caused disturbances, so that existing forest cover types are more a result of ecological processes rather than forest management practices.

# for sake of time is 1/4th of the data
subset = x.shape[0]//4
x = x[:subset,:]
y = y[:subset]

# Is this computed on GPU or on Host? Remember compute follows data
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=72)

#########  Add code to get GPU context and set flag if GPU is available   #######
#########  Add code to to set CPU context as well so this runs on eiher device   #######
# for d in dpctl.get_devices():
#     gpu_available = False
#     for d in dpctl.get_devices():
#         if d.is_gpu:
#             gpu_device = dpctl.select_gpu_device()
#             gpu_available = True
#         else:
#             cpu_device = dpctl.select_cpu_device() 
# if gpu_available:
#     print("GPU targeted: ", gpu_device)
# else:
#     print("CPU targeted: ", cpu_device)
#########################################################################################

device = dpctl.select_default_device()
print("Using device ...")
device.print_device_info()


# if gpu_available:
    ################## add code to cast from Numpy to dpctl_tensors #########################    # target a remote host GPU when submitted via q.sh or qsub -I
x_train_device = dpctl.tensor.asarray(x_train, usm_type = 'device', device = device)
y_train_device = dpctl.tensor.asarray(y_train, usm_type = 'device', device = device)
x_test_device = dpctl.tensor.asarray(x_test, usm_type = 'device', device = device)
y_test_device = dpctl.tensor.asarray(y_test, usm_type = 'device', device = device)
    ##########################################################################################
# else:
#     ################## add code to cast from Numpy to dpctl_tensors for Host CPU ####################    # target a remote host GPU when submitted via q.sh or qsub -I    
#     # target a remote host CPU when submitted via q.sh or qsub -I
#     x_train_device = dpctl.tensor.asarray(x_train, usm_type = 'device', device = "cpu")
#     y_train_device = dpctl.tensor.asarray(y_train, usm_type = 'device', device = "cpu")
#     x_test_device = dpctl.tensor.asarray(x_test, usm_type = 'device', device = "cpu")
#     y_test_device = dpctl.tensor.asarray(y_test, usm_type = 'device', device = "cpu")
    ##########################################################################################

params = {
    'n_neighbors': 40,  
    'weights': 'distance'
}
print('dataset shape: ', x_train_device.shape)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
#from sklearn.neighbors import KNeighborsClassifier
#LR = KNeighborsClassifier(**params).fit(x_train_device, y_train_device)
#clf = LogisticRegression(random_state=0, solver='lbfgs').fit(x_train_device, y_train_device) # or lbfgs

TestingString = "RandomForestClassifier"
clf = RandomForestClassifier(random_state=0).fit(x_train_device, y_train_device) 
predictedGPU = clf.predict(x_test_device) #Predict on GPU
predictedCPU = clf.predict(x_test) #Predict on CPU
predictedGPUNumpy = dpctl.tensor.to_numpy(predictedGPU)

################## add code to cast returned results to Numpy to dpctl_tensors ################  
# only need to do this for predict. fit_predict, transform, fit_transform IF I need to use results
# target a remote host GPU when submitted via q.sh or qsub -I    
predictedGPUNumpy = dpctl.tensor.to_numpy(predictedGPU)
###############################################################################################

reportGPU = metrics.classification_report(y_test, predictedGPUNumpy)
print(f"Classification report for {TestingString} Fit and Predicted on GPU:\n{reportGPU}\n")

reportCPU = metrics.classification_report(y_test, predictedCPU)
print(f"Classification report for {TestingString}  Fit on GPU and Predicted on CPU:\n{reportCPU}\n")
