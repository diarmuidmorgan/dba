
import pandas as pd
class stop_link_model():
    """
    Refactoring of simple model.
    Want to add - 
    a) options for polynomial features
    b) Options for ignoring dwell time models
    c) Options for different regressors
    
    """
    
    def __init__(self,from_stop,to_stop,data,clf='Linear',\
                dimension=1,model_dwell_time=True,\
                train_test=None,alpha=0.0001,\
                model_weather=False):
        """
        Choose the regressor (clf should be regressor sorry) used to model dwelltime and travel time.
        More regressors can be implemented as 'elif' statements.
        """
        self.train_test=train_test
        self.model_dwell_time=model_dwell_time
        self.dimension = dimension
        self.model_weather = model_weather
        if clf =='Linear':
            from sklearn.linear_model import LinearRegression
            self.clf = LinearRegression(fit_intercept=True)
        elif clf=='Neural':
            from sklearn.neural_network import MLPRegressor
            self.clf = MLPRegressor(hidden_layer_sizes=(100,), alpha=alpha)
        elif clf =='Svm':
            from sklearn.svm import SVR
            self.clf = SVR()
        elif clf == 'RandomForest':
            from sklearn.ensemble import RandomForestRegressor
            from subprocess import call
            call(['killall','python'])

        self.from_stop = from_stop
        self.to_stop = to_stop
        self.data = data
        #for validation, we can decide what kind of train test split to do. The default is to just train
        #on all of the data
        if train_test!=None:
            if train_test == 'random':
                import numpy as np
                msk = np.random.rand(len(self.data)) < 0.8
                self.data = self.data[msk]
            elif train_test == 'year':
                data = self.data[self.data['year']==2016]
                print(data.shape)
                if data.shape[0] > 100:
                    self.data = data
                else:
                    import numpy as np
                    msk = np.random.rand(len(self.data)) < 0.8
                    self.data = self.data[msk]
        if self.dimension == 2:
            self.data['hour'] = self.data['actualtime_arr_from']//3600
            self.data['hour2'] - self.data['hour']**2
        elif self.dimension == 3:
            self.data['hour'] = self.data['actualtime_arr_from']//3600
            self.data['hour2'] = self.data['hour']**2
            self.data['hour3'] = self.data['hour']**3
        #allow the option here for not modelling dwell time
        if model_dwell_time:        
            self.buildDwellTimeModel()
            self.buildTravelModel()
        else:
            self.buildTravelModel(dwell_time=False)
        #delete data to ensure RAM efficiency
        del(self.data)

    def buildDwellTimeModel(self):
        #train a single regressor for dwell time
        
        target = 'actualtime_dep_from'
        features = ['actualtime_arr_from','dayofweek','month','weekend']
        #add polynomial features if required
        if self.dimension > 1:
            features += ['hour','hour2']
            if self.dimension > 2:
                features+=['hour3']
        if self.model_weather:
            #add weather features here
            features += ['rain','temp']
        self.dwell_regr = self.clf.fit(self.data[features],self.data[target])
    def buildTravelModel(self,dwell_time=True):
        #train a single regressor for travel time
        target = 'actualtime_arr_to'
        if dwell_time:
            features = ['actualtime_dep_from','dayofweek','month','weekend']
        else:
            #if we are not including a dwell time model, then travel time will just use arrival time at
            #a to predict arrival time at b
            features = ['actualtime_arr_from','dayofweek','month','weekend']
        #add polynomial features as required
        if self.dimension > 1:
            features += ['hour','hour2']
            if self.dimension > 2:
                features += ['hour3']
        if self.model_weather:
            features += ['rain','temp']

        self.travel_regr=self.clf.fit(self.data[features],self.data[target])
     
    def get_time_to_next_stop(self, arrival_time, dayofweek,month,weekend):
        
        """
        Get predictions for dwell time and travel time and sum them together to get the time to the next stop"
        
        this method if DEPRECATED. We aren't using it in the current prototype, and it probably doesn't even
        work. Use get_time_to_next_stop_multiple instead.
        """
        
        index1 = ['actualtime_arr_from','dayofweek','month','weekend']
        index2 = ['actualtime_dep_from','dayofweek','month','weekend']
        row = pd.DataFrame([[arrival_time,dayofweek,month,weekend]],index=index1)
        leavetime = self.dwell_regr.predict(row)[0]
        row2 = pd.DataFrame([[leavetime,dayofweek,month,weekend]],index=index2)
        arrival_time = self.travel_regr.predict(row2)[0]
        return arrival_time
    
    def get_time_to_next_stop_multiple(self,df):
        
        """
        Same as above, but for a matrix containing multiple times.
        Returns a dataframe that can be used as a timetable.
        """
        features1 = ['actualtime_arr_from', 'dayofweek','month','weekend']
        features2 = ['actualtime_dep_from','dayofweek','month','weekend']
        
        #add polynomial features if required
        if self.dimension > 1:

            df['hour'] = df['actualtime_arr_from'] // 3600
            df['hour2'] = df['hour'] ** 2
            features1 += ['hour','hour2']
            features2 += ['hour','hour2']

            if self.dimension >2:
                df['hour3'] = df['hour'] ** 3
                features1+=['hour3']
                features2+=['hour3']
                    
        if self.model_dwell_time:
            #two fold modelling. Get dwell time first, and then use that to model travel time.
            df['actualtime_dep_from']=self.dwell_regr.predict(\
                                df[features1])
            df['actualtime_arr_to'] = self.travel_regr.predict(\
                                df[features2])
            return df
        else:
            #Just make a single prediction for travel time.
            df['actualtime_arr_to'] = self.travel_regr.predict(df[features1])
            return df


        
                    
